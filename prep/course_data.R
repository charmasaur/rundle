library(XML)
library(sf)
library(dplyr)
library(geosphere)

source("prep_functions.R")

path <- "C:/Users/admin/Documents/Running/_Rundle"

files <- tools::file_path_sans_ext(list.files(path, pattern = "gpx"))

starts <- sapply(files, makePlots, path = path)

starts.sf <- data.frame(x = starts[1,],
                        y = starts[2,],
                        course = colnames(starts)) %>%
  st_as_sf(coords = c("x", "y"), crs = 4326) %>%
  st_transform(crs = 3577)
  
# create a distance matrix
dist.m <- round(st_distance(starts.sf)/1000, 0) %>%
  units::drop_units()

rownames(dist.m) <- files
colnames(dist.m) <- files

write.csv(dist.m, file.path(path, "distance_matrix.csv"))

## turn it into a df
# dist.names <- expand.grid(starts.sf$course, starts.sf$course,
#                           stringsAsFactors = F)
# dist.names <- dist.names[as.vector(upper.tri(dist.m, diag = F)),]
# 
# dist.df <- data.frame(dist.names, stringsAsFactors = F) %>%
#   mutate(distkm = dist.m[lower.tri(dist.m, diag = F)]) %>%
#   rename(from = Var1,
#          to = Var2)
# 
# write.csv(dist.df, file.path(path, "distance_matrix.csv"))

# create a direction matrix
starts.t <- t(starts)

bear.m <- getBearingsFromCoords(starts.t)

rownames(bear.m) <- files
colnames(bear.m) <- files

write.csv(bear.m, file.path(path, "bearing_matrix.csv"))


## turn into a df
# b.names <- expand.grid(starts.sf$course, starts.sf$course,
#                           stringsAsFactors = F)
# b.names <- b.names[as.vector(upper.tri(bear.m, diag = F)),]
# 
# bear.df <- data.frame(b.names, stringsAsFactors = F) %>%
#   mutate(bearing = bear.m[lower.tri(bear.m, diag = F)]) %>%
#   rename(from = Var1,
#          to = Var2)
# 
# write.csv(bear.df, file.path(path, "bearing_matrix.csv"))
