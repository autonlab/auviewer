#!/usr/bin/env python3
"""
Normalize files.path values to top-level project-local originals paths.

The AUViewer loader briefly stored resolved symlink targets instead of the
project-local symlink paths. That makes links in different projects collide
with a global UNIQUE constraint on files.path.

This tool is dry-run by default. Pass --apply to update the database. Apply
mode creates a SQLite backup before opening a write transaction. The optional
--replace-prefix OLD NEW argument also migrates projects.path and writes
project-local files.path values below NEW.
"""

import argparse
import datetime as dt
import os
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileRow:
    file_id: int
    project_id: int
    project_name: str
    project_path: str
    stored_path: str


@dataclass(frozen=True)
class PathChange:
    row: FileRow
    normalized_path: str
    match_method: str


@dataclass(frozen=True)
class ProjectPathChange:
    project_id: int
    project_name: str
    stored_path: str
    normalized_path: str


def absolute_path(path):
    """Return an absolute path without dereferencing symlinks."""
    return Path(os.path.abspath(os.fspath(path)))


def file_identity(path):
    """Return the physical identity used by os.path.samefile()."""
    stat_result = path.stat()
    return stat_result.st_dev, stat_result.st_ino


def replace_path_prefix(path, old_prefix, new_prefix):
    """Replace an exact path-component prefix without resolving symlinks."""
    path = absolute_path(path)
    if old_prefix is None:
        return path
    try:
        relative_path = path.relative_to(old_prefix)
    except ValueError:
        return path
    return new_prefix / relative_path


def path_is_within(path, directory):
    """Return whether path is equal to or below directory."""
    try:
        absolute_path(path).relative_to(absolute_path(directory))
    except ValueError:
        return False
    return True


def database_path(path_argument):
    path = absolute_path(Path(path_argument).expanduser())
    if path.is_dir():
        path = path / "database" / "db.sqlite"
    if not path.is_file():
        raise FileNotFoundError(f"SQLite database not found: {path}")
    return path


def load_rows(connection, project_ids):
    parameters = []
    project_filter = ""
    if project_ids:
        placeholders = ", ".join("?" for _ in project_ids)
        project_filter = f"WHERE f.project_id IN ({placeholders})"
        parameters.extend(project_ids)

    return [
        FileRow(*row)
        for row in connection.execute(
            f"""
            SELECT f.id, f.project_id, p.name, p.path, f.path
            FROM files AS f
            JOIN projects AS p ON p.id = f.project_id
            {project_filter}
            ORDER BY f.project_id, f.id
            """,
            parameters,
        )
    ]


def load_projects(connection, project_ids):
    parameters = []
    project_filter = ""
    if project_ids:
        placeholders = ", ".join("?" for _ in project_ids)
        project_filter = f"WHERE id IN ({placeholders})"
        parameters.extend(project_ids)

    return list(
        connection.execute(
            f"""
            SELECT id, name, path
            FROM projects
            {project_filter}
            ORDER BY id
            """,
            parameters,
        )
    )


def index_project_originals(project_path):
    originals_path = absolute_path(project_path) / "originals"
    if not originals_path.is_dir():
        raise FileNotFoundError(
            f"Project originals directory not found: {originals_path}"
        )

    identities = {}
    names = {}
    warnings = []

    # Deliberately inspect only direct children. AUViewer does not recursively
    # discover files under originals.
    for entry in originals_path.iterdir():
        entry = absolute_path(entry)
        try:
            if not entry.is_file() or entry.suffix != ".h5":
                continue
            identity = file_identity(entry)
        except OSError as error:
            warnings.append(f"Could not inspect {entry}: {error}")
            continue

        identities.setdefault(identity, []).append(entry)
        names.setdefault(entry.name, []).append(entry)

    return identities, names, warnings


def plan_changes(connection, project_ids, old_prefix=None, new_prefix=None):
    rows = load_rows(connection, project_ids)
    projects = load_projects(connection, project_ids)
    all_path_owners = {
        path: file_id
        for file_id, path in connection.execute("SELECT id, path FROM files")
    }
    project_indexes = {}
    effective_project_paths = {}
    path_changes = []
    project_path_changes = []
    warnings = []
    unchanged = 0

    for project_id, project_name, stored_project_path in projects:
        normalized_project_path = replace_path_prefix(
            stored_project_path, old_prefix, new_prefix
        )

        if str(normalized_project_path) != stored_project_path:
            if not normalized_project_path.is_dir():
                warnings.append(
                    f"project_id={project_id} ({project_name!r}): prefix "
                    f"replacement destination does not exist: "
                    f"{normalized_project_path}; project and file paths were "
                    "left unchanged"
                )
                effective_project_paths[project_id] = absolute_path(
                    stored_project_path
                )
                continue

            project_path_changes.append(
                ProjectPathChange(
                    project_id=project_id,
                    project_name=project_name,
                    stored_path=stored_project_path,
                    normalized_path=str(normalized_project_path),
                )
            )

        effective_project_paths[project_id] = normalized_project_path

    for row in rows:
        if row.project_id not in project_indexes:
            try:
                project_indexes[row.project_id] = index_project_originals(
                    effective_project_paths.get(
                        row.project_id, absolute_path(row.project_path)
                    )
                )
            except OSError as error:
                project_indexes[row.project_id] = None
                warnings.append(
                    f"project_id={row.project_id} ({row.project_name!r}): {error}"
                )

        project_index = project_indexes[row.project_id]
        if project_index is None:
            continue

        identities, names, index_warnings = project_index
        if index_warnings:
            warnings.extend(
                f"project_id={row.project_id}: {warning}"
                for warning in index_warnings
            )
            # Emit per-project indexing warnings only once.
            project_indexes[row.project_id] = identities, names, []

        stored_path = absolute_path(row.stored_path)
        candidates = []
        match_method = ""

        try:
            candidates = identities.get(file_identity(stored_path), [])
            if candidates:
                match_method = "physical file identity"
        except OSError:
            # Mount migrations can make an old stored path inaccessible. The
            # deployment guarantees that symlink names equal target filenames,
            # so an unambiguous top-level basename is a safe fallback.
            candidates = names.get(stored_path.name, [])
            if candidates:
                match_method = "filename fallback (stored path is inaccessible)"

        if not candidates:
            prefix_rewritten_path = replace_path_prefix(
                row.stored_path, old_prefix, new_prefix
            )
            if str(prefix_rewritten_path) == row.stored_path:
                warnings.append(
                    f"file_id={row.file_id} project_id={row.project_id}: no "
                    f"top-level project file matches {row.stored_path}"
                )
                continue

            same_name_candidates = names.get(stored_path.name, [])
            if same_name_candidates:
                warnings.append(
                    f"file_id={row.file_id} project_id={row.project_id}: "
                    f"top-level project path has the same filename but points "
                    f"to a different physical file: "
                    f"{[str(path) for path in same_name_candidates]}"
                )
                continue

            project_originals_path = (
                effective_project_paths[row.project_id] / "originals"
            )

            if path_is_within(prefix_rewritten_path, project_originals_path):
                # The old row was already project-local; only its retired
                # mount prefix needs to change.
                normalized_path = str(prefix_rewritten_path)
                match_method = (
                    "mount-prefix fallback "
                    "(project file is currently missing)"
                )
            else:
                # A resolved target path outside the owning project may
                # collide with another project's legacy row. Preserve this
                # row's ID and foreign-key references by restoring its
                # project-local identity using the guaranteed-identical
                # filename, even if the symlink is currently absent.
                normalized_path = str(
                    project_originals_path / stored_path.name
                )
                match_method = (
                    "owning-project path fallback "
                    "(project file is currently missing)"
                )
        elif len(candidates) != 1:
            warnings.append(
                f"file_id={row.file_id} project_id={row.project_id}: "
                f"ambiguous match for {row.stored_path}: "
                f"{[str(path) for path in candidates]}"
            )
            continue
        else:
            normalized_path = str(candidates[0])

        if row.stored_path == normalized_path:
            unchanged += 1
            continue

        conflicting_file_id = all_path_owners.get(normalized_path)
        if (
            conflicting_file_id is not None
            and conflicting_file_id != row.file_id
        ):
            warnings.append(
                f"file_id={row.file_id} project_id={row.project_id}: cannot "
                f"change to {normalized_path}; that path is already owned by "
                f"file_id={conflicting_file_id}"
            )
            continue

        path_changes.append(
            PathChange(
                row=row,
                normalized_path=normalized_path,
                match_method=match_method,
            )
        )
        all_path_owners.pop(row.stored_path, None)
        all_path_owners[normalized_path] = row.file_id

    return (
        rows,
        path_changes,
        project_path_changes,
        warnings,
        unchanged,
    )


def create_backup(connection, source_path, requested_path):
    if requested_path:
        backup_path = absolute_path(Path(requested_path).expanduser())
    else:
        timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_path = Path(f"{source_path}.backup-{timestamp}")

    if backup_path.exists():
        raise FileExistsError(f"Backup path already exists: {backup_path}")

    backup_connection = sqlite3.connect(str(backup_path))
    try:
        connection.backup(backup_connection)
    finally:
        backup_connection.close()
    return backup_path


def apply_changes(connection, path_changes, project_path_changes):
    connection.execute("BEGIN IMMEDIATE")
    try:
        for change in path_changes:
            cursor = connection.execute(
                """
                UPDATE files
                SET path = ?
                WHERE id = ? AND project_id = ? AND path = ?
                """,
                (
                    change.normalized_path,
                    change.row.file_id,
                    change.row.project_id,
                    change.row.stored_path,
                ),
            )
            if cursor.rowcount != 1:
                raise RuntimeError(
                    f"file_id={change.row.file_id} changed after the dry-run "
                    "plan was built; no updates were committed"
                )

        for change in project_path_changes:
            cursor = connection.execute(
                """
                UPDATE projects
                SET path = ?
                WHERE id = ? AND path = ?
                """,
                (
                    change.normalized_path,
                    change.project_id,
                    change.stored_path,
                ),
            )
            if cursor.rowcount != 1:
                raise RuntimeError(
                    f"project_id={change.project_id} changed after the dry-run "
                    "plan was built; no updates were committed"
                )

        connection.commit()
    except Exception:
        connection.rollback()
        raise


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description=(
            "Normalize AUViewer files.path rows to their top-level "
            "project-local originals paths. Defaults to a read-only dry-run."
        )
    )
    parser.add_argument(
        "data_or_database_path",
        help=(
            "AUViewer data directory (containing database/db.sqlite) or the "
            "db.sqlite path itself"
        ),
    )
    parser.add_argument(
        "--project-id",
        type=int,
        action="append",
        dest="project_ids",
        help="Only inspect this owning project ID; may be repeated",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Create a backup and apply the displayed changes",
    )
    parser.add_argument(
        "--backup",
        help="Backup destination used with --apply (default: timestamped path)",
    )
    parser.add_argument(
        "--replace-prefix",
        nargs=2,
        metavar=("OLD", "NEW"),
        help=(
            "Also rewrite projects.path and normalized files.path from OLD "
            "to NEW, using path-component-aware prefix matching"
        ),
    )
    args = parser.parse_args(argv)
    if args.backup and not args.apply:
        parser.error("--backup requires --apply")
    return args


def main(argv=None):
    args = parse_args(argv)

    try:
        db_path = database_path(args.data_or_database_path)
    except (FileNotFoundError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    connection = sqlite3.connect(str(db_path), timeout=30)
    try:
        if args.replace_prefix:
            old_prefix = absolute_path(Path(args.replace_prefix[0]).expanduser())
            new_prefix = absolute_path(Path(args.replace_prefix[1]).expanduser())
        else:
            old_prefix = None
            new_prefix = None

        (
            rows,
            path_changes,
            project_path_changes,
            warnings,
            unchanged,
        ) = plan_changes(
            connection,
            args.project_ids,
            old_prefix,
            new_prefix,
        )

        print(f"Database: {db_path}")
        print(
            f"Inspected {len(rows)} file rows: {len(path_changes)} file path "
            f"change(s), {len(project_path_changes)} project path change(s), "
            f"{unchanged} file path(s) already normalized, "
            f"{len(warnings)} warning(s)."
        )

        for change in project_path_changes:
            print(
                "\nPROJECT CHANGE "
                f"project_id={change.project_id} "
                f"project={change.project_name!r}\n"
                f"  from: {change.stored_path}\n"
                f"  to:   {change.normalized_path}"
            )

        for change in path_changes:
            print(
                "\nFILE CHANGE "
                f"file_id={change.row.file_id} "
                f"project_id={change.row.project_id} "
                f"project={change.row.project_name!r}\n"
                f"  from: {change.row.stored_path}\n"
                f"  to:   {change.normalized_path}\n"
                f"  match: {change.match_method}"
            )

        for warning in warnings:
            print(f"\nWARNING: {warning}", file=sys.stderr)

        if not args.apply:
            print(
                "\nDRY RUN: no database changes were made. "
                "Re-run with --apply after reviewing every CHANGE."
            )
            return 0

        if not path_changes and not project_path_changes:
            print("\nNo applicable changes; no backup or write was performed.")
            return 0

        backup_path = create_backup(connection, db_path, args.backup)
        print(f"\nBackup created: {backup_path}")
        apply_changes(connection, path_changes, project_path_changes)
        print(
            f"Applied {len(path_changes)} file path change(s) and "
            f"{len(project_path_changes)} project path change(s) successfully."
        )
        return 0
    except (OSError, sqlite3.Error, RuntimeError) as error:
        print(f"\nERROR: {error}", file=sys.stderr)
        return 1
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
