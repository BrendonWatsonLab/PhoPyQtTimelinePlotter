import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from time import sleep

val1 = np.zeros(100)
val2 = np.zeros(100)

level1 = 0.2
level2 = 0.5

fig, ax = plt.subplots()

ax1 = plt.subplot2grid((2,1),(0,0))
lineVal1, = ax1.plot(np.zeros(100))
ax1.set_ylim(-0.5, 1.5)

ax2 = plt.subplot2grid((2,1),(1,0))
lineVal2, = ax2.plot(np.zeros(100), color = "r")
ax2.set_ylim(-0.5, 1.5)


def onMouseMove(event):
  ax1.lines = ax1.lines[:2] # keep the first two lines
  ax1.axvline(x=event.xdata, color="k") # then draw the vertical line



def updateData():
  global level1, val1
  global level2, val2

  clamp = lambda n, minn, maxn: max(min(maxn, n), minn)

  level1 = clamp(level1 + (np.random.random()-.5)/20.0, 0.0, 1.0)
  level2 = clamp(level2 + (np.random.random()-.5)/10.0, 0.0, 1.0)

  # values are appended to the respective arrays which keep the last 100 readings
  val1 = np.append(val1, level1)[-100:]
  val2 = np.append(val2, level2)[-100:]

  yield 1     # FuncAnimation expects an iterator

def visualize(i):

  lineVal1.set_ydata(val1)
  lineVal2.set_ydata(val2)

  return lineVal1,lineVal2

fig.canvas.mpl_connect('motion_notify_event', onMouseMove)
ani = animation.FuncAnimation(fig, visualize, updateData, interval=50)
plt.show()