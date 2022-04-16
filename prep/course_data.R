library(sf)
library(dplyr)
library(geosphere)
library(plotKML)
library(purrr)
library(tidyr)

source("prep_functions.R")

path <- "C:/Users/admin/Documents/Running/_Rundle"

gpxNames <- tools::file_path_sans_ext(list.files(path, pattern = "gpx"))
files <- list.files(path, pattern = "gpx", full.names = T)

# read gpx
gpx <- map(files,
           readGPX) %>%
  map(., function(x) x$tracks[[1]]) %>%
  map(., function(x) x[[1]]) %>%
  set_names(nm = gpxNames) %>%
  map(., dplyr::mutate, ele = as.numeric(ele))

# get start locations
starts <- map(gpx, dplyr::select, lon, lat) %>%
  map(., dplyr::slice_head, n = 1) %>%
  dplyr::bind_rows(.id = "courseCode")

# get distances
dists <- map(gpx, function(x) gpxDistance(x)) %>%
  bind_rows(.id = "courseCode") %>%
  pivot_longer(cols = everything(),
               names_to = "courseCode",
               values_to = "dist")

# get elevations
elevs <- map(gpx, function(x) gpxElevation(x$ele)) %>%
  bind_rows(.id = "courseCode") %>%
  pivot_longer(cols = everything(),
               names_to = "courseCode",
               values_to = "elev")

# save basic course data
course.df <- starts %>%
  left_join(dists, by = "courseCode") %>%
  left_join(elevs, by = "courseCode") %>%
  select(courseCode,
         lat,
         lon,
         dist,
         elev) %>%
  mutate(concat = paste(lat, lon, dist, elev, sep = "|"))

write.csv(course.df, file.path(path, "course_overview.csv"))


# create plots
## course plot
map2(gpx, gpxNames, function(x, y) plotCourse(lon = x$lon,
                                              lat = x$lat,
                                              courseName = y,
                                              path = path))

map2(gpx, gpxNames, function(x, y) plotElevation(elev = x$ele,
                                                      courseName = y,
                                                      path = path))

# Distance matrix
starts.sf <- starts %>%
  st_as_sf(coords = c("lon", "lat"), crs = 4326) %>%
  st_transform(crs = 3577)

dist.m <- round(st_distance(starts.sf)/1000, 0) %>%
  units::drop_units()

rownames(dist.m) <- files
colnames(dist.m) <- files

write.csv(dist.m, file.path(path, "distance_matrix.csv"))


# Bearing matrix
starts.m <- matrix(c(starts$lon, starts$lat), ncol = 2)

bear.m <- getBearingsFromCoords(starts.m)

rownames(bear.m) <- gpxNames
colnames(bear.m) <- gpxNames

write.csv(bear.m, file.path(path, "bearing_matrix.csv"))
