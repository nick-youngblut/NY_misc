#!/usr/bin/env r

# a simple example to install one or more packages

suppressMessages(library(docopt))       # we need the docopt package 0.3 or later

doc <- "Usage: rInstallPackages.r [-r REPO] [-l LIBLOC] [-h] [PACKAGES ...]

-r --repos REPO     Repository to install from [default: http://cran.rstudio.com]
-l --libloc LIBLOC  Location in which to install [default: /usr/local/lib/R/site-library]
-h --help           Show this help text"

opt <- docopt(doc)

install.packages(pkgs  = opt[["PACKAGES"]],
                 lib   = opt[["libloc"]],
                 repos = opt[["repos"]],
                 dependencies=TRUE)

q(status=0)
