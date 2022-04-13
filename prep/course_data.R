library(XML)
library(sf)
library(dplyr)
library(geosphere)
library(plotKML)
library(purrr)
library(tidyr)

source("prep_functions.R")

path <- "C:/Users/admin/Documents/Running/_Rundle"

files <- tools::file_path_sans_ext(list.files(path, pattern = "gpx"))
gpxNames <- file.path(path, paste0(files, ".gpx"))

# read gpx
gpx <- map(gpxNames[1:3],
           readGPX) %>%
  map(., function(x) x$tracks[[1]]) %>%
  map(., function(x) x[[1]]) %>%
  set_names(nm = files[1:3]) %>%
  map(., dplyr::mutate, ele = as.numeric(ele))

# get start locations
starts <- map(gpx, dplyr::select, lon, lat) %>%
  map(., dplyr::slice_head, n = 1) %>%
  dplyr::bind_rows(.id = "courseCode")

# get distances
dists <- map(gpx, function(x) gpxDistance(x)) %>%
  bind_rows(.id = "courseCode")

# get elevations
elevs <- map(gpx, function(x) gpxElevation(x$ele)) %>%
  bind_rows(.id = "courseCode")

# create plots
##### Up to here with revisions ######


# make and save some plots
starts <- sapply(files, makePlots, path = path)

# create a simple features object for distance calcs
starts.sf <- data.frame(x = starts[1,],
                        y = starts[2,],
                        course = colnames(starts)) %>%
  st_as_sf(coords = c("x", "y"), crs = 4326)

# create a distance matrix
starts.alb <- st_transform(starts.sf, crs = 3577)

dist.m <- round(st_distance(starts.alb)/1000, 0) %>%
  units::drop_units()

rownames(dist.m) <- files
colnames(dist.m) <- files

write.csv(dist.m, file.path(path, "distance_matrix.csv"))

# create a direction matrix
starts.t <- t(starts)

bear.m <- getBearingsFromCoords(starts.t)

rownames(bear.m) <- files
colnames(bear.m) <- files

write.csv(bear.m, file.path(path, "bearing_matrix.csv"))

# save start coordinates
colnames(starts.t) <- c("x", "y")

write.csv(starts.t, file.path(path, "start_coords.csv"))
