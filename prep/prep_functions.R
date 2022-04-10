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

makePlots <- function(file, path){
  # make a course map, a raw elevation profile, and a scaled elevation profile
  # file = name of the .gpx file, without the file extension
  # path = path to folder containing gpx files
  
  # parse xml
  gfile <- htmlTreeParse(file.path(path, paste0(file, ".gpx")),
                         useInternalNodes = T)
  
  # coords
  coords <- xpathSApply(gfile, path = "//trkpt", xmlAttrs)
  
  lats <- as.numeric(coords["lat",])
  lons <- as.numeric(coords["lon",])
  
  # get start lat/lon
  start <- c(lons[1], lats[1])
  
  # elevation
  elev <- as.numeric(xpathSApply(gfile, path = "//trkpt/ele", xmlValue))
  
  if(length(elev) != 0){ # sometimes the gpx doesn't have elevation
    # put into data frame
    gdf <- data.frame(row = c(1:length(elev)),
                      elev = elev,
                      lat = lats,
                      lon = lons) %>%
      mutate(elev.l = lowess(elev, f = 0.001)$y)
    
    # make some plots
    ## elevation
    svg(file.path(path, paste0(file, "_elev.svg")))
    
    plot(gdf$elev.l, 
         type = "l", 
         bty = "n", 
         ylab = "", 
         xlab = "", 
         col = "grey40",
         axes = F,
         lwd = 2)
    
    dev.off()
    
    ## scaled elevation
    svg(file.path(path, paste0(file, "_elev_scaled.svg")))
    
    plot(gdf$elev.l, 
         type = "l", 
         bty = "n", 
         ylab = "", 
         xlab = "", 
         col = "grey40",
         axes = F,
         lwd = 2,
         ylim = c(min(gdf$elev.l), min(gdf$elev.l)+1500))
    
    polygon(c(1, 1:nrow(gdf), nrow(gdf)+1),
            c(min(gdf$elev.l), gdf$elev.l, min(gdf$elev.l)),
            col="grey", 
            border=F)
    
    dev.off()
    
    ## map
    svg(file.path(path, paste0(file, "_course.svg")))
    
    plot(rev(gdf$lon), 
         rev(gdf$lat), 
         type = "l", 
         col = "red", 
         lwd = 2, 
         bty = "n",
         axes = F,
         xlab = "",
         ylab = "")
    
    dev.off()
  }
  
  return(start)
}