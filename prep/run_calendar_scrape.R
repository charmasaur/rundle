install.packages("rvest")
library(rvest)
library(dplyr)

test <- read_html("https://www.runningcalendar.com.au/calendar/?y=1&a=16.17.18.19.20&df=2022-04-06&dt=2024-01-31")

main <- "https://www.runningcalendar.com.au/calendar/?y=1&a=16.17.18.19.20&df=2022-04-06&dt=2024-01-31"

runList <- list()

for(i in 1:8){
  temp <- read_html(paste0(main, "&page=", i)) %>%
    html_nodes("a") %>%
    html_text()
  
  start <- which(temp == "our levels of membership") + 1
  end <- max(which(temp == "Save search") - 1)
  
  runList[[i]] <- temp[start:end]
}

runDF <- data.frame("eventName" = unlist(runList)) %>%
  distinct()

write.csv(runDF, "run_calendar_list.csv", row.names = T)

## To do:
# clean years from run names
# try go get distances from running calendar
