#require("pacman")
#pacman::p_load(zoo, plyr, reshape, MASS, nlts, strucchange, np, data.table, doParallel)

lapply(c('zoo', 'plyr', 'reshape', 'MASS', 'nlts', 'strucchange', 'np', 'data.table', 'doParallel'), require, character.only = TRUE)

#library(auton.utils)
registerDoParallel(cores=8)

write.csv.na <- function(ob, filename) {
	fwrite(ob, file=filename, quote=F, sep=',', row.names=F, na='')
}


import.csv <- function(filename) {
	return(fread(file=filename, sep=',', header=T, stringsAsFactors=F))
}

write.csv <- function(ob, filename) {
	fwrite(ob, file=filename, quote=F, sep=',', row.names=F)
}

time_min <-function (t1,t2) { return(min(t1, t2, na.rm=T)) }
time_max <-function (t1,t2) { return(max(t1, t2, na.rm=T)) }

# t1 <- alert.df[1,2]
# t2 <- alert.df[1,3]
# scope1 <- raw.start
# scope2 <- raw.end
# max_range <- 720
get_range <- function(t1,t2,scope1,scope2,max_range=720){
	t0 <- strptime('01/01/2000 09:00:00',format='%m/%d/%Y %H:%M',tz='UTC')
	d1 <- difftime(t1,t0,units='mins')
	d2 <- difftime(t2,t0,units='mins')
	d <- (d1+d2)/2
	mid_t <- t0+d
	
	range.min <- time_max(scope1,mid_t-(max_range/2)*60)
	range.max <- time_min(scope2,mid_t+(max_range/2)*60)
	
	return(list(min=range.min,max=range.max))
}


remove_duplicate <- function(df){
	return (df[!duplicated(df),])
}



get_slope <- function(x,y){
	X <- x
	Y <- y  
	result <-  tryCatch(as.numeric(coef(lm(Y~X))[2]),error = function(e) {NA})
	return(result)
}



get_robust_slope <- function(x,y){
	X <- x
	Y <- y
	print('x')
	print(X)
	print('y')
	print(Y)

#     print("BEGIN")
# 	print(rlm(X, Y))
# 	print("COEF")
# 	print(coef(rlm(X, Y)))
# 	print("COEF[2]")
# 	print(coef(rlm(X, Y))[1])
# 	print("DONE")
# 	return(NA)

# 	result <- tryCatch(as.numeric(coef(rlm(Y~X))[2]), error = function(e) { print(e); return(NA); })
	result <- tryCatch(as.numeric(coef(rlm(Y~X))[1]), error = function(e) { print(e); return(NA); })
	print("result")
	print(result)
	return(result)
}


get_slope_break <- function(x,y){
	
	slope1 <- NA
	slope2 <- NA
	Nb <- NA
	
	NN <- sum(1*(!is.na(y))) # number of non-missing value
	if (NN>5){
		fs <- Fstats(y~x)
		bp <- fs$breakpoint
		if (length(bp)>0){
			idx1 <- 1:bp
			idx2 <- bp:length(x)
			slope1 <- get_slope(x[idx1],y[idx1])
			slope2 <- get_slope(x[idx2],y[idx2])
			Nb <- length(bp)
		}
		else {slope1 <- get_slope(x,y)
		slope2 <- get_slope(x,y) 
		Nb <- 0
		}
	}
	return(list(slope1,slope2,break_point=Nb))
}





#x: relative time index (don't need to be evenly spaced)
#y: value
get_spectral_lomb <-function(x,y){
	non_missing <- which(!is.na(y))
	x1 <- x[non_missing]
	y1 <- y[non_missing]
	fit <- tryCatch({spec.lomb(y1,x1)},
		warning=function(w) {},
		error=function(e) {print(geterrormessage());print("FAIL! (error)");return(NA)}                   
	)
	
	ratio <- NA
	max_spec <- NA
	if (!is.null(fit))
	{ratio <- max(fit$spec)/median(fit$spec)
	max_spec <- max(fit$spec)
	}
	stat <- list(ratio,max_spec)
	return(stat)
	
}

#rsquare for a quardatic fit
get_rsq <- function(X,Y){
	if (sum(!is.na(Y))<20){
		out <- list(rsq=NA,coef1=NA,coef2=NA,var.res=NA)
	}
	else{
		fit <- lm(Y~X+I(X^2),na.action='na.omit')
		var.res <- var(fit$residuals)
		rsq <-  1-var.res/var(Y,na.rm=TRUE)
		coef1 <- as.numeric(coef(fit)[1])
		coef2 <- as.numeric(coef(fit)[2])
		out <- list(rsq=rsq,coef1=coef1,coef2=coef2,var.res=var.res)
	}
	return(out)
}



#F test for nested model
#R.lm simple moder
#F.lm higher order model
f.test.lm <- function(R.lm, F.lm) {
	SSE.R <- sum(resid(R.lm)^2)
	SSE.F <- sum(resid(F.lm)^2)
	df.num <- R.lm$df - F.lm$df
	df.den <- F.lm$df
	F <- ((SSE.R - SSE.F) / df.num) / (SSE.F / df.den)
	p.value <- 1 - pf(F, df.num, df.den)
	return(data.table(F, df.num, df.den, p.value))
}



do.Ftest.qr <- function(value){
	X <-  1:length(value)
	Y <- value
	#df <- f.test.lm(lm(Y~1),lm(Y~X+I(X^2)))
	
	df <-  tryCatch(f.test.lm(lm(Y~1),lm(Y~X+I(X^2))),error = function(e) {NULL})
	if (!is.null(df)){
		F.lm <- lm(Y~X+I(X^2))
		coef_A <- coef(F.lm)[2]
		coef_B <- coef(F.lm)[3]
		pvalue <- df$p.value
		stat <- df$F
	}else {
		coef_A <- NA
		coef_B <- NA
		pvalue <- NA
		stat <- NA
	}
	return(data.table(pvalue,stat,coef_A,coef_B))  
}


do.Ftest.lm <- function(X,Y){
	
	R.lm <- lm(Y~1)
	F.lm <- lm(Y~X)
	df <- f.test.lm(R.lm,F.lm)
	
	result <-  tryCatch(as.numeric(coef(lm(Y~X))[2]),error = function(e) {NA})
	#return(result)
	
	return(data.table(pvalue=df$p.value,stat=df$F))  
}




MAD <- function(x){
	x1 <- x[which(!is.na(x))]
	med <- median(x)
	result <- median(abs(x-med))
	return(result)                  
}

get.osci.index <- function(x,y,x_thresh=5, y_thresh=10){
	df <- data.table(x,y)
	df <- subset(df,!is.na(y))
	diff.df <- with(df,data.table(x=diff(x,difference=1),y=diff(y,difference=1)))
	up <- nrow(subset(diff.df,x<x_thresh & y>y_thresh))
	down <- nrow(subset(diff.df, x<x_thresh & y< -1*y_thresh))
	ratio <- up/(up+down)
	return(list(up=up,down=down,ratio=ratio))    
}




bi.hr <- function(x)
{
	y=ifelse(is.na(x),0, 1*((1*(x<40)+1*(x>140))>0))
	return(y)  
}

bi.rr <- function(x)
{
	y=ifelse(is.na(x),0, 1*((1*(x<8)+1*(x>36))>0))
	return(y)  
}


bi.sp <- function(x)
{
	y=ifelse(is.na(x),0,1*(x<85))
	return(y)  
}

bi.sbp <- function(x)
{
	y=ifelse(is.na(x),0, 1*((1*(x<80)+1*(x>200))>0))
	return(y)   
}

bi.dbp <- function(x)
{
	y=ifelse(is.na(x),0,1*(x>110))
	return(y)     
}

avail <- function(x){
	y <- 1*(!is.na(x))
	return(y)
}

roll.na <- function(dt, keep.na.rows=F)
{
	dt[, (colnames(dt)) := lapply(.SD, zoo::na.locf, na.rm=F)]
	if (!keep.na.rows) dt <- na.omit(dt)
	return(dt)
}


doit <- function(dt.vitals, dt.alerts=NULL, downsample.interval=-1)
{
	file.path <- 'input/P3_by_visits_update/'
	
	
	alarm.file.path <- './'
	
	if (is.null(dt.alerts)) {
		dt.alerts <- import.csv(paste0(alarm.file.path, "input/alarm_tol40_length180_pctg60.csv"))
		colnames(dt.alerts)[which(colnames(dt.alerts) == "fn_id")] <- "visit"
		colnames(dt.alerts)[which(colnames(dt.alerts) == "start_time")] <- "st"
		colnames(dt.alerts)[which(colnames(dt.alerts) == "end_time")  ] <- "et"
		
		dt.alerts[, st := as.POSIXct(st, tz='UTC')]
		dt.alerts[, et   := as.POSIXct(et  , tz='UTC')]
		dt.alerts[, downsampling := -1]
	}
	
	#debug
	visits <- dt.alerts[, sort(as.character(unique(visit)))]
	
	#out <- NULL
	#for (visit.i in visits)
	out <- foreach (visit.i = visits, .combine='rbind') %do%
	{
		print(sprintf('--::==[ %s (%d of %d) ]==::--',
			visit.i, which(visits == visit.i), length(visits)))
		alert.df <- dt.alerts[
			visit == visit.i &
			(downsampling %in% c(-1, downsample.interval)) &
			label != 'Unlabelled']
		
		fn <- paste0(file.path, unique(alert.df$visit), '.csv')
		
		raw.data <- copy(dt.vitals[visit == visit.i])
		raw.data[, reltime := as.double(time - time[1], units='secs')]
		raw.data <- roll.na(raw.data)
		raw.data <- raw.data[downsample.series(reltime, interval=downsample.interval)]
		raw.data[, PP := SysBP - DiaBP]
		
		#for (ii in alert.df[, seq_len(.N)])
		out.alert <- foreach (ii = alert.df[, seq_len(.N)], .combine='rbind') %dopar%
		{
			alert_str <- alert.df[ii, as.character(alert_id)]
			vital <- alert.df[ii, as.character(vital)]
			alert_label <- alert.df[ii, as.character(label)]
			
			#cat(' - Alert', ii, '-',alert_str,' (', alert_label, ')\n')
			
			alert.start <- alert.df[ii, st]
			alert.end <- alert.df[ii, et]
			
			my.range <- list(min=alert.start, max=alert.end)
			mydata <- raw.data[time >= my.range$min & time <= my.range$max]
			
			small.window <- ifelse(downsample.interval >  4*60, downsample.interval*2,  4*60)
			big.window   <- ifelse(downsample.interval > 15*60, downsample.interval*2, 15*60)
			
			my.range2 <- list(min=alert.start - small.window, max=alert.start) #4 min before alert
			mydata2 <- raw.data[time >= my.range2$min & time <= my.range2$max]
			
			my.range3 <- list(min=alert.start - small.window, max=alert.start + small.window) #4 min and 4 min after
			mydata3 <- raw.data[time >= my.range3$min & time <= my.range3$max]
			
			my.range4 <- list(min=alert.start - big.window, max=alert.start) #15 min before alert
			mydata4 <- raw.data[time >= my.range4$min & time <= my.range4$max]
			
			#binary flag count within alert period
			bi.mydata <- mydata[, .(time, HR=bi.hr(HR),RR=bi.rr(RR),SPO2=bi.sp(SPO2), SysBP=bi.sbp(SysBP), DiaBP=bi.dbp(DiaBP))]
			
			flag.count <- colSums(bi.mydata[,-1]) 
			
			var.list <- setdiff(colnames(mydata), c('visit', 'time', 'reltime'))
			
			#for (var.name in var.list)
			out.alert.var <- foreach (var.name = var.list, .combine='rbind') %do%
			{
				#cat('  -', var.name, '...\n')
				#binary flag count within alert period
				if (var.name %in% c('HR','RR','SPO2','SysBP', 'DiaBP' )) {
					my.flag.count=flag.count[var.name]
				} else {
					my.flag.count=-1
				}
				
				Y <- mydata[[var.name]]
				#Y[which(Y==0)] <- NA  #set value=0 as NA
				X <- mydata$reltime
				nn_non_missing<- sum(!is.na(Y))
				
				
				
				#quadratic model fitting result
				quad.fit <- get_rsq(X,Y)
				quad_rsq <- quad.fit$rsq
				quad_coef1 <- quad.fit$coef1
				quad_coef2 <- quad.fit$coef2
				quad_resvar <- quad.fit$var.res
				
				
				
				slope <- get_slope(X,Y)
				rslope <- get_robust_slope(X,Y)
				
				#slope assuming there is structual change      
				break_slope <- get_slope_break(X,Y)
				slope1 <- break_slope[[1]]
				slope2 <- break_slope[[2]]
				num_breakpoint <- break_slope$break_point
				
				mean <- mean(Y,na.rm=TRUE)
				median <- median(Y, na.rm=TRUE)
				
				
				sd <- sd(Y, na.rm=TRUE)
				mad <- MAD(Y) #median of absolute deviation
				cv <- sd/mean  #coefficent of variance  1/SNR
				min <- min(Y, na.rm=TRUE)
				max <- max(Y, na.rm=TRUE)
				range <- max-min
				range_ratio <- range/median
				
				#oscilation index
				osi.index <- get.osci.index(X,Y)
				osi_up <- osi.index$up
				osi_down <- osi.index$down
				osi_ratio <- osi.index$ratio
				
				
				
				#data density
				X.non.missing <- X[which(!is.na(Y))]
				data.den <- length(unique(X.non.missing))/(max(X, na.rm=T)-min(X, na.rm=T))
				
				#1st order difference
				diff.X <- diff(X.non.missing,difference=1)
				max_gap <- max(diff.X, na.rm=T)
				
				time_length <- difftime(alert.end,alert.start,units='mins')
				#       
				#       #spectrum features
				#       spec.stat <- get_spectral_lomb(X,Y)
				#       spec_ratio <- spec.stat[[1]]
				#       max_spec <- spec.stat[[2]]
				
				
				#       #time since chunk start
				#       var.name2 <- ifelse(var.name %in% c( "SysBP","DiaBP","MeanBP","PP"),'SysBP',var.name )
				#       delta_t <- delta.df$delta_t[(delta.df$fn_id==fn.id)&(delta.df$ii==ii)&(delta.df$att_name==var.name2)]
				#       #delta_t <- 0
				
				
				#difference in mean before and after
				delta_mean <- mean(mydata[[var.name]],na.rm=TRUE) - mean(mydata2[[var.name]],na.rm=TRUE)
				delta_sd <- sd(mydata[[var.name]],na.rm=TRUE) - sd(mydata2[[var.name]],na.rm=TRUE)
				
				
				
				
				var1 <- mydata[[var.name]] #after
				var0 <- mydata2[[var.name]] #before
				
				t_stat <- NA
				t_pvalue <- NA
				F_stat <- NA
				F_pvalue <- NA
				
				MW_stat <- NA
				MW_pvalue <- NA
				KS_stat <- NA
				KS_pvalue <- NA
				if((sum(1*(!is.na(var1)))>5)*(sum(1*(!is.na(var0)))>5)) {
					MW_test <- wilcox.test(var1,var0,na.action='na.omit')
					MW_stat <- MW_test$statistic
					MW_pvalue <- MW_test$p.value #log pvalue
					
					#Kolmogorov-Smirnov test
					KS_test <- ks.test(var1,var0)
					KS_stat <- KS_test$statistic
					KS_pvalue <- KS_test$p.value
					
					if (var(var1,na.rm=TRUE)*var(var0,na.rm=TRUE)>0){  # prevent zero variance 
						#t test - Normal assumption
						t_test <- t.test(var1,var0)
						t_stat <- t_test$statistic
						t_pvalue <- t_test$p.value
						
						#F test for difference of variance - Normal assumption
						F_test <- var.test(var1,var0)
						F_stat <- F_test$statistic
						F_pvalue <- F_test$p.value
					}
				}
				
				#1st diff min and max deltaY/deltaX, if deltaX=0, set deltax=1
				Y3 <- mydata3[[var.name]]
				YY3 <- Y3[which(!is.na(Y3))]
				XY3 <- mydata3[!is.na(Y3), c('reltime',var.name), with=F]
				
				if(nrow(XY3)>0){
					diff.df <- XY3[, lapply(.SD, diff)]
					names(diff.df) <- c('x', 'y')
					diff.df[x == 0, x := 1]
					diff1 <- diff.df[, y/x]
					diff1_max <- max(diff1, na.rm=T)
					diff1_min <- min(diff1, na.rm=T)
				} else {
					diff1_max=NA
					diff1_min=NA
				}
				
				if (length(YY3)>0){
					diff1_max <- max(diff(ts(YY3)), na.rm=T)
					diff1_min <- min(diff(ts(YY3)), na.rm=T)
					
				} else {
					diff1_max=NA
					diff1_min=NA
				}
				
				#moving slope in window - min/max (4 min before and 4 min after) - alternative to 
				XY3 <- mydata3[!is.na(Y3), c('reltime',var.name), with=F]
				max_grad <- NA
				min_grad <- NA
				if (nrow(XY3)>5) {
					np.grad <-npreg(XY3[[2]] ~ XY3[[1]], gradient=TRUE)$grad
					max_grad <- max(np.grad, na.rm=T)
					min_grad <- min(np.grad, na.rm=T)
				}
				
				
				#                     
				#trailing data density at the beginning of alert (for 15 min before the start of alert)
				XY4 <- mydata4[, c('reltime',var.name), with=F]
				X4 <- XY4[[1]]
				Y4 <- XY4[[2]]
				data_den_trail <- sum(1*!is.na(Y4))/(max(X4, na.rm=T)-min(X4, na.rm=T))
				data_den_trail2 <- sum(1*!is.na(Y4))/(15*60) # avg number of data points in 15 min
				
				#                   
				#       
				#       this.stat <- rbind(this.stat, data.table(att_name=var.name,slope,rslope,slope1,slope2,mean,sd,mad,cv,data_den=data.den,spec_ratio,
				#                                                max_spec,delta_t,N=nn_non_missing,num_breakpoint,max_gap,
				#                                                min,max,median,range,range_ratio,time_length,
				#                                                delta_mean,delta_sd,diff1_max,diff1_min,max_grad,min_grad,
				#                                                data_den_trail,data_den_trail2,
				#                                                MW_stat,MW_pvalue,KS_stat,KS_pvalue,
				#                                                quad_rsq,quad_coef1,quad_coef2,quad_resvar,osi_up,osi_down,osi_ratio,
				#                                                t_stat,t_pvalue,F_stat,F_pvalue, flag_count=my.flag.count ))
				
				#this.stat <- rbind(
				#	this.stat,
				return(data.table(
					att_name=var.name,
					label=alert_label,
					slope, mean, sd, mad, cv,
					data_den=data.den,	  
					N=nn_non_missing, max_gap,
					rslope, slope1, slope2, num_breakpoint,
					min, max, median, range, range_ratio, time_length,
					delta_mean, delta_sd, diff1_max, diff1_min, max_grad,min_grad,
					data_den_trail, data_den_trail2,
					MW_stat, MW_pvalue, KS_stat, KS_pvalue,
					t_stat, t_pvalue, F_stat, F_pvalue,												
					quad_rsq, quad_coef1, quad_coef2, quad_resvar, osi_up, osi_down, osi_ratio,
					flag_count=my.flag.count))
			} #variable
			
			m.stat <- melt(out.alert.var, c('att_name', 'label'))
			m.stat[, (c('visit', 'alert_str', 'vital')) := .(
				visit.i, alert_str, vital)]
			#out <-rbind(out, m.stat)
			return(m.stat)
		} # alert
		
		return(out.alert)
	}
	
	out.dir <- paste0('output.', downsample.interval)
	if (!dir.exists(out.dir))
		dir.create(out.dir)
	
	out[is.infinite(value), value := NA]
	feats <- dcast(out, visit + alert_str + label ~ att_name + variable)
	fwrite(feats[, -('alert_str'), with=F], sprintf('%s/merged_features.csv', out.dir))
	
	# write.csv(out, sprintf('%s/feature_out.csv', out.dir))
	# out <- import.csv(sprintf('%s/feature_out.csv', out.dir))
	# 
	# replace_inf <- function(x,replace=NA){
	# 	x[is.infinite(x)]=replace
	# 	return(x)
	# }
	# 
	# out$value <- replace_inf(out$value)
	# #out2 <- out[which(!is.na(out$value)),]
	# out2 <- out
	# 
	# #transform to short data
	# long.data <- out2
	# att_str <- with(long.data, paste0(att_name,'-',variable))
	# id <- with(long.data, paste0(visit,'-',ii))
	# 
	# lookup <- unique(data.table(id,long.data[,c(1,2,3,4)]))
	# 
	# long.data2 <- data.table(id,att_str,value=long.data$value)
	# 
	# short.data <- reshape(long.data2, idvar='id',direction='wide',v.names='value',timevar='att_str',sep='-')
	# 
	# short.data.expand <- join(short.data,lookup,type='left')
	# 
	# write.csv.na(short.data.expand, sprintf('%s/alert_feature_short_format_complete_set.csv', out.dir))
	# write.csv(out2, sprintf('%s/alert_feature_long_format.csv', out.dir))
	# 
	# 
	# #debug
	
	# # 
	# # 
	# # 
	# # #to trim the feature 
	# short.data.expand <- import.csv('alert_feature_short_format_complete_set.csv')
	# feature.lookup <- import.csv('short_format_variable_lookup.csv')
	# jitter.list <- feature.lookup$var_name[which(feature.lookup$jitter=='Y')]
	# 
	# 
	# for (var.name in jitter.list){
	#   print(var.name)
	#   jitter <- runif(nrow(short.data.expand))/3
	#   short.data.expand[,var.name] <- short.data.expand[,var.name]+jitter
	# }
	# 
	# 
	# keep.list <- feature.lookup$var_name[which(feature.lookup$remove=='N')]
	# short.data.trimed <- short.data.expand[,keep.list]
	# write.csv.na(short.data.trimed, 'alert_feature_short_format_trimmed_jittered.csv')
	# 
	# 
	# #do jittering on selected variables
}
comp_grads <- function(x, y) {
    np.grad <-npreg(y~x, gradient=TRUE)$grad
    min_grad <- min(np.grad, na.rm=T)
    max_grad <- max(np.grad, na.rm=T)
    return(list(min_grad=min_grad,max_grad=max_grad))
}
