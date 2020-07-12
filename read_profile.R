require("ggplot2")
require("mgcv")

f_profile<-choose.files()

df<-read.csv(f_profile)
df<-df[order(df$ID, decreasing=TRUE),]
df$DIST<-abs(df$DIST-max(df$DIST))
df$DIST_SURF<-abs(df$DIST_SURF-max(df$DIST_SURF))
df$DIST<- (df$DIST / 1000)
df$DIST_SURF<- df$DIST_SURF / 1000
#View(df)

main_plot<-ggplot(df)+geom_line( aes(x=DIST_SURF, y=Z), color="red") 
main_plot<- main_plot+ xlab("Distance from confluence with Ogooué (km)") + ylab("elevation (m)")
main_plot<- main_plot + ggtitle("Lubimbi river profile") +  theme_classic() + theme(plot.title = element_text(hjust = 0.5))
#print(main_plot)

df2 <- data.frame(x=df$DIST_SURF, y=df$Z)

## Set up the size of the basis functions/number of knots
k <- 20
## This fits the unconstrained model but gets us smoothness parameters that
## that we will need later
unc <- gam(y ~ s(x, k = k, bs = "cr"), data = df2)

## This creates the cubic spline basis functions of `x`
## It returns an object containing the penalty matrix for the spline
## among other things; see ?smooth.construct for description of each
## element in the returned object
sm <- smoothCon(s(x, k = k, bs = "cr"), df2, knots = NULL)[[1]]

## This gets the constraint matrix and constraint vector that imposes
## linear constraints to enforce montonicity on a cubic regression spline
## the key thing you need to change is `up`.
## `up = TRUE` == increasing function
## `up = FALSE` == decreasing function (as per your example)
## `xp` is a vector of knot locations that we get back from smoothCon
F <- mono.con(sm$xp, up = TRUE)   # get constraints: up = FALSE == Decreasing constraint!

## Fill in G, the object pcsl needs to fit; this is just what `pcls` says it needs:
## X is the model matrix (of the basis functions)
## C is the identifiability constraints - no constraints needed here
##   for the single smooth
## sp are the smoothness parameters from the unconstrained GAM
## p/xp are the knot locations again, but negated for a decreasing function
## y is the response data
## w are weights and this is fancy code for a vector of 1s of length(y)
G <- list(X = sm$X, C = matrix(0,0,0), sp = unc$sp,
          p = sm$xp, # - for decreasing
          y = df2$y,
          w = df2$y*0+1)
G$Ain <- F$A    # the monotonicity constraint matrix
G$bin <- F$b    # the monotonicity constraint vector, both from mono.con
G$S <- sm$S     # the penalty matrix for the cubic spline
G$off <- 0      # location of offsets in the penalty matrix

## Do the constrained fit 
p <- pcls(G)  # fit spline (using s.p. from unconstrained fit)

## predict at 100 locations over range of x - get a smooth line on the plot
newx <- with(df2, data.frame(x = seq(min(x), max(x), length = max(df$Z))))

fv <- Predict.matrix(sm, newx) %*% p
newx <- transform(newx, yhat = fv[,1])

plot(y ~ x, data = df2, pch = 16)
lines(yhat ~ x, data = newx, col = "red")

