##GMM.py: functions for calculating gaussian mixture models

from sklearn import metrics
from sklearn.mixture import GMM
import numpy as np
import matplotlib.pyplot as plt

def generate_gmm(data):
	##reshape the data
	X = data.reshape(data.shape[0], 1)
	##fit models with 1-10 components
	N = np.arange(1,11)
	models = [None for i in range(len(N))]
	for i in range(len(N)):
		models[i] = GMM(N[i]).fit(X)
	##compute AIC
	AIC = [m.aic(X) for m in models]
	##figure out the best-fit mixture
	M_best = models[np.argmin(AIC)]
	x = np.linspace(data.min(), data.max(), data.size)
	##compute the pdf
	logprob, responsibilities = M_best.score_samples(x.reshape(x.size, 1))
	pdf = np.exp(logprob)
	pdf_individual = responsibilities * pdf[:, np.newaxis]
	##plot the stuff
	# fig, ax = plt.subplots()
	# ax.hist(X, 50, normed = True, histtype = 'stepfilled', alpha = 0.4)
	# ax.plot(x, pdf, '-k')
	# ax.plot(x, pdf_individual, '--k')
	# ax.text(0.04, 0.96, "Best-fit Mixture",
 #        ha='left', va='top', transform=ax.transAxes)
	# ax.set_xlabel('$x$')
	# ax.set_ylabel('$p(x)$')
	return x, pdf, pdf_individual



##this function takes in an array of x-values and an array
##of y-values that correspond to a probability density function
##and determines the x-value at which the area under the PDF is approximately
##equal to some value passed in the arguments.
def prob_under_pdf(x_pdf, y_pdf, prob):
	auc = 0
	i = 2
	while auc < prob:
		x_range = x_pdf[0:i]
		y_range = y_pdf[0:i]
		auc = metrics.auc(x_range, y_range)
		i+=1
	return x_pdf[i]
