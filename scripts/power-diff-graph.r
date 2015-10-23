library('ggplot2')

input = "../arm-power-comparison/diff_vs_length.csv"
output = "../arm-power-comparison/diff_vs_length.png"

df = read.csv(input)
# Columns in df: Seconds, Difference
summary(df)

# WORKS BUT INAPPROPRIATE: Polynomial regression: fit and confidence band
#qplot(Seconds, Difference, data=df, geom=c("point", "smooth"), method="lm", formula= y ~ poly(x, 2)) + xlab("Length of interval with compared samples, Seconds") + ylab("Difference between cumulative CM and on-node power, %")

png(output,height=600,width=800)
ggplot(df, aes(x = Seconds, y = Difference, group = Seconds)) + 
  geom_boxplot() + 
  stat_summary(fun.y=median, geom="line",aes(group=1),color="red") +
  xlab("Length of interval with compared samples, Seconds") + 
  ylab("Difference between cumulative CM and on-node power, %") + 
  ggtitle("Comparing CM and on-node power measurements") +
  theme(axis.text = element_text(size = 15)) +
  theme(axis.title = element_text(size = 20)) +
  theme(text = element_text(size = 25))

dev.off()
