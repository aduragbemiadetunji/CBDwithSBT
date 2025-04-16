import numpy as np
import matplotlib.pyplot as plt

def drawHeart(x):
    a = np.sin((np.pi**3)*x)
    b = (np.sqrt(np.exp(2) - x**2))/2
    c = np.sqrt(np.abs(x))

    y = a * b + c
    # print(y)
    return y

x = np.linspace(-3, 3, 10000)
y = drawHeart(x)



plt.plot(x, y, c='red')
plt.show()