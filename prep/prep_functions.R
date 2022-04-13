getBearingsFromCoords <- function(coords){
  #coords is a matrix with cols x, y
  #one row for each location
  #names for locations
  
  b.list <- list()
  
  for(i in 1:nrow(coords)){
    b.list[[i]] <- bearing(coords[i,], coords)
  }
  
  names(b.list) <- paste0("C", c(1:nrow(coords)))
  
  b.df <- bind_rows(b.list) %>%
    data.matrix()
  
  return(b.df)
  
}

plotCourse <- function(lon, lat, courseName){
  # plot a course map
  # lon = vector of longitudes
  # lat = vector of latitudes
  # courseName = name for the course that will be used in the file name
  
  svg(file.path(path, paste0(courseName, "_course.svg")))
  
  plot(rev(lon), 
       rev(lat), 
       type = "l", 
       col = "red", 
       lwd = 2, 
       bty = "n",
       axes = F,
       xlab = "",
       ylab = "")
  
  dev.off()
  
}

plotElevation <- function(elev, courseName, scaled = T){
  # plot an elevation profile
  # elev = vector of elevations
  # courseName = name for the course that will be used in the file name
  elev.l = lowess(elev, f = 0.001)$y
  
  if(scaled){y = elev.l} else {y = elev}
  
  svg(file.path(path, paste0(file, "_elev_scaled.svg")))
  
  plot(y, 
       type = "l", 
       bty = "n", 
       ylab = "", 
       xlab = "", 
       col = "grey40",
       axes = F,
       lwd = 2,
       ylim = c(min(y), min(y)+1500))
  
  polygon(c(1, 1:length(y), length(y+1)),
          c(min(y), y, min(y)),
          col="grey", 
          border=F)
  
  dev.off()
  
}

gpxDistance <- function(lonLatDF){
  # get the course distance
  # lonLatDF is a data frame with columns 'lon' and 'lat'
  df <- lonLatDF %>%
    dplyr::mutate(nextX = lead(lon, n = 1),
           nextY = lead(lat, n = 1))

  dist <- pmap(select(df, lon, lat, nextX, nextY),
               function(lon, lat, nextX, nextY) raster::pointDistance(c(lon, lat),
                                     c(nextX, nextY),
                                     lonlat = T)) %>%
    unlist()
  
  totalDist <- round(sum(dist, na.rm = T)/1000, 1)
  
  return(totalDist)
}

gpxElevation <- function(elev){
  # get the course elevation gain
  nextE <- lead(elev, 1)
  diffE <- elev - nextE
  totalE <- round(sum(diffE[which(diffE > 0)]), 0)
  return(totalE)
}
