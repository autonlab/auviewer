import os
import openai
import importlib
from auviewer import lfs

openai.api_key_path="/Users/qingyang/desktop/AutonLab/resuscitation-project/openai_api_key.txt"


lfs_list = [] # the list of LFs to be global?
lfs_dict = {}
fname = 'auviewer/lfs.py' # global?


def check_answer(answer):
    # Check if the answer string returned by GPT starts with 'def '
    if (answer.find("def ") != 0): return None #raise Exception("Answer not Python function: def")
    # Possible handle: add some to the prompt to the gpt message and ask again

    # Check if the answer string returned by GPT has one input pig and valid syntax for input
    para_index = answer.find("(pig):")
    if (para_index == -1): return None # raise Exception("Answer not Python function: one parameter pig")

    # Manual check if answer string returned by GPT ends with a 'return 0/1'
    if (not answer.endswith("return SUFFICIENT") and not answer.endswith("return ABSTAIN") and not answer.endswith("return NOT_SUFFICIENT")):
        return None # raise Exception("Answer not Python function: not end with return 0/1")
    
    lf_name = answer[len("def "):para_index] # Get LF function name as a string [after "def ", before "(pig):"]
    
    if (lf_name in lfs_dict): return None # raise Exception("Function name already exist") !!!! Fix this, give user message about function name!

    return (lf_name, answer)


# Source: https://platform.openai.com/docs/guides/gpt

def run_conversation(request):
    system_message = '''We are trying to convert a definition of medical sufficiency condition for pigs into a labeling function that will later be used in a Snorkel labeling model. 
Here is the context: each pig data have some statistics available, including 
pig['baseline_ART'], pig['ART_5_Min'] which is the persistence of ART in the past five minutes, 
pig['ART_mean [1 min]'], pig['ART_mean [2 min]'], pig['ART_mean [5 min]'], pig['ART_mean [10 min]'], pig['ART_mean [15 min]'], pig['baseline_SvO2'], pig['SvO2_mean [1 min]'], 
pig['SvO2_mean [2 min]'], pig['SvO2_mean [5 min]'], pig['SvO2_mean [10 min]'], pig['SvO2_mean [15 min]'],
pig['baseline_HR'], pig['HR_mean [1 min]'], pig['HR_mean [2 min]'], pig['HR_mean [5 min]'], pig['HR_mean [10 min]'], pig['HR_mean [15 min]']. (HR means Heart rate)
Return a labeling function in python that is ready to be used and nothing else. It needs to take in an argument called pig, and return SUFFICIENT in the condition specified by user, return ABSTAIN otherwise. 
'''
    user_message1 = '''SvO2 mean in the past two minutes is greater than or equal to target, where target is the lower one between SvO2 baseline and 65, but not lower than 60 . Function name: SvO2_mean_condition'''
    assistant_message1 = '''def SvO2_mean_condition(pig):
    target = min(pig['baseline_SvO2'], 65)
    target = max(target, 60)
    
    if pig['SvO2_mean [2 min]'] >= target:
        return SUFFICIENT
    else:
        return ABSTAIN
'''

    messages=[
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message1},
        {"role": "assistant", "content": assistant_message1},
        {"role": "user", "content": request}
    ]
    # Call GPT API
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.5,     
    )

    answer = response["choices"][0]["message"]["content"]
    
    finish_reason = response["choices"][0]["finish_reason"]

    # Regenerate if finish reason is not stop
    while finish_reason != "stop":
        response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.5, 
        )
        answer = response["choices"][0]["message"]["content"]
        finish_reason = response["choices"][0]["finish_reason"]    

    return answer


def process_lf(lf_name, lf_str):
    lfs_dict[lf_name] = lf_str

    with open(fname, 'a') as f: # append the LF to the lfs.py
        f.write("\n\n")
        f.write("@labeling_function()")
        f.write("\n")
        f.write(lf_str)
    
    importlib.reload(lfs)

    lf_function = getattr(lfs, lf_name, None)

    lfs_list.append(lf_function)

    return list(lfs_dict.keys())
    

def general_GPT(request):
    gpt_answer = run_conversation(request)
    check_result = check_answer(gpt_answer)
    if check_result != None:
        lf_name, lf_str = check_result
        return lf_name, lf_str
    else:
        return None





# request = "the persistence of ART in the past 5 minutes should be greater than or equal to 0.75. Function name: ART_persistence_check"
# request = "the average of heart rate in the past 2 mins should be less than 110. Function name: HR mean upperbound"
# lf_str = run_conversation(request)
# print(lf_str)

# Example returned lf string:
# "def ART_persistence_check(pig):\n    if pig['ART_5_Min'] >= 0.75:\n        return 1\n    else:\n        return 0"


# answer = "def ART_test(pig):\n    if pig >= 0:\n        return 1\n    else:\n        return 0"
# process_lf(answer)
# process_lf(answer)








