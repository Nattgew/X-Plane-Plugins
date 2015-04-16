from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt

m = Basemap(projection='hammer',lon_0=180)
m.shadedrelief()
colors=['b','g','r','c','m','k']
#for i in range(len(divs)):
#	print("Plotting division "+str(i))
#	for j in range(len(divs[i])):
#		print("Plotting coord "+str(divs[i][j][0])+", "+str(divs[i][j][1]))
i=0
x, y = m(-104.784,31.0578)
m.scatter(x,y,5,marker='o',color=colors[i])
plt.title('Locations of airports divided into regions',fontsize=12)
plt.show()
