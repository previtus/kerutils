from __future__ import print_function
from keras.models import Sequential
from keras.layers.core import Dense, Dropout
from keras.callbacks import Callback
from matplotlib import pyplot as plt
import numpy as np
import warnings
from .imgutils import *
# fixed random seed for reproducibility
np.random.seed(0)

class FitMonitor(Callback):
    def __init__(self, **opt):
        super(Callback, self).__init__()
        #Callback.__init__(self)
        self.thresh = opt.get('thresh', 0.02) # max difference between loss and val_loss for saving model
        self.maxloss = opt.get('maxloss', 0.01) # minimal loss for model saving
        self.best_loss = self.maxloss
        self.filename = opt.get('filename', None)
        self.verbose = opt.get('verbose', 1)
        self.checkpoint = None
        self.stop_file = 'stop_training_file.keras'
        self.pause_file = 'pause_training_file.keras'
        self.hist = {'acc': [], 'loss': [], 'val_acc': [], 'val_loss': []}

    def on_epoch_begin(self, epoch, logs={}):
        #print("epoch begin:", epoch)
        self.curr_epoch = epoch

    def on_train_begin(self, logs={}):
        "This is the point where training is starting. Good place to put all initializations"
        self.start_time = datetime.datetime.now()
        t = datetime.datetime.strftime(self.start_time, '%Y-%m-%d %H:%M:%S')
        print("Train begin:", t)
        print("Stop file: %s (create this file to stop training gracefully)" % self.stop_file)
        print("Pause file: %s (create this file to pause training and view graphs)" % self.pause_file)
        self.print_params()
        self.progress = 0
        self.max_acc = 0
        self.max_val_acc = -1
        self.min_loss = 1
        self.min_val_loss = 1
        self.min_loss_epoch = -1
        self.min_val_loss_epoch = -1

    def on_train_end(self, logs={}):
        "This is the point where training is ending. Good place to summarize calculations"
        self.end_time = datetime.datetime.now()
        t = datetime.datetime.strftime(self.end_time, '%Y-%m-%d %H:%M:%S')
        print("Train end:", t)
        dt = self.end_time - self.start_time
        if self.verbose:
            time_str = format_time(dt.total_seconds())
            print("Total run time:", time_str)
            print("min_loss = %f  epoch = %d" % (self.min_loss, self.min_loss_epoch))
            print("min_val_loss = %f  epoch = %d" % (self.min_val_loss, self.min_val_loss_epoch))
        if self.filename:
            if self.checkpoint:
                print("Best model saved in file:", self.filename)
                print("Checkpoint: epoch=%d, loss=%.6f, val_loss=%.6f" % self.checkpoint)
            else:
                print("No checkpoint model found.")
                #print("Saving the last state:", self.filename)
                #self.model.save(self.filename)

    def on_batch_end(self, batch, logs={}):
        #print("epoch=%d, batch=%s, loss=%f" % (self.curr_epoch, batch, logs.get('loss')))
        #self.probe(logs)
        if os.path.exists(self.pause_file):
            os.remove(self.pause_file)
            self.plot_hist()

    def on_epoch_end(self, epoch, logs={}):
        acc = logs.get('acc')
        val_acc = logs.get('val_acc', -1)
        loss = logs.get('loss')
        val_loss = logs.get('val_loss', -1)
        self.hist['acc'].append(acc)
        self.hist['loss'].append(loss)
        if val_acc != -1:
            self.hist['val_acc'].append(val_acc)
            self.hist['val_loss'].append(val_loss)

        #print(self.params)
        p = int(epoch / (self.params['epochs'] / 100.0))
        if p > self.progress:
            sys.stdout.write('.')
            if p%5 == 0:
                dt = datetime.datetime.now() - self.start_time
                time_str = format_time(dt.total_seconds())
                fmt = '%02d%% epoch=%d, loss=%f, val_loss=%f, time=%s\n'
                vals = (p,    epoch,    loss,    val_loss,    time_str)

                sys.stdout.write(fmt % vals)
            sys.stdout.flush()
            self.progress = p
        if epoch == self.params['epochs'] - 1:
            sys.stdout.write(' %d%% epoch=%d loss=%f\n' % (p, epoch, loss))

        self.probe(logs)

    def probe(self, logs):
        epoch = self.curr_epoch
        acc = logs.get('acc')
        val_acc = logs.get('val_acc', -1)
        loss = logs.get('loss')
        val_loss = logs.get('val_loss', -1)
        if os.path.exists(self.stop_file):
            os.remove(self.stop_file)
            self.model.stop_training = True

        if os.path.exists(self.pause_file):
            os.remove(self.pause_file)
            self.plot_hist()

        if val_loss < self.min_val_loss:
            self.min_val_loss = val_loss
            self.min_val_loss_epoch = epoch

        #print (loss, self.min_loss)
        if loss < self.min_loss:
            self.min_loss = loss
            self.min_loss_epoch = epoch

            #print(self.min_loss_epoch, self.min_loss)
            if self.filename != None:
                if loss < self.best_loss and (val_loss == -1 or abs(val_loss - loss) <= self.thresh):
                    print("\nSaving model to %s: epoch=%d, loss=%f, val_loss=%f" % (self.filename, epoch, loss, val_loss))
                    self.model.save(self.filename)
                    self.checkpoint = (epoch, loss, val_loss)
                    self.best_loss = loss

        self.max_acc = max(self.max_acc, acc)

    def plot_hist(self):
        #loss, acc = self.model.evaluate(X_train, Y_train, verbose=0)
        #print("Training: accuracy   = %.6f loss = %.6f" % (acc, loss))
        #X = m.validation_data[0]
        #Y = m.validation_data[1]
        #loss, acc = self.model.evaluate(X, Y))
        #print("Validation: accuracy = %.6f loss = %.6f" % (acc, loss))
        # Accuracy history graph
        plt.plot(self.hist['acc'])
        plt.title('model accuracy')
        plt.ylabel('accuracy')
        plt.xlabel('epoch')
        if self.hist['val_acc']:
            plt.plot(self.hist['val_acc'])
            leg = plt.legend(['train', 'validation'], loc='best')
            plt.setp(leg.get_lines(), linewidth=3.0)
        plt.show()
        plt.plot(self.hist['loss'])
        plt.title('model loss')
        plt.ylabel('loss')
        plt.xlabel('epoch')
        if self.hist['val_loss']:
            plt.plot(self.hist['val_loss'])
            leg = plt.legend(['train', 'validation'], loc='best')
            plt.setp(leg.get_lines(), linewidth=3.0)
        plt.show()

    def print_params(self):
        for key in sorted(self.params.keys()):
            print("%s = %s" % (key, self.params[key]))

#-------------------------------------------------------------

class BreakOnMonitor(Callback):
    def __init__(self, monitor='loss', value=0.8, epoch_limit=30, verbose=1):
        super(Callback, self).__init__()
        self.monitor = monitor
        self.value = value
        self.epoch_limit = epoch_limit
        self.verbose = verbose
        self.max_value = 0
        self.stop_file = 'stop_training_file.keras'

    def on_train_begin(self, logs={}):
        print("Stop file: %s (create this file to stop training gracefully)" % self.stop_file)

    def on_epoch_end(self, epoch, logs={}):
        curr_loss = logs.get(self.monitor)
        if curr_loss is None:
            warnings.warn("Early stopping requires %s available!" % self.monitor, RuntimeWarning)

        if curr_loss < self.min_value:
            self.min_value = curr_loss

        if epoch > self.epoch_limit and self.min_value < self.value:
            if self.verbose > 0:
                print("\nEARLY STOPPING: epoch=%d ; No monitor progress" % epoch)
            self.model.stop_training = True

        if os.path.exists(self.stop_file):
            os.remove(self.stop_file)
            self.model.stop_training = True

#-------------------------------------------------------------

# h - history object returned by Keras model method
def show_scores(model, h, X_train, Y_train, X_test, Y_test):
    #print( h.params )

    loss, acc = model.evaluate(X_train, Y_train, verbose=0)
    print("Training: accuracy   = %.6f loss = %.6f" % (acc, loss))
    loss, acc = model.evaluate(X_test, Y_test, verbose=0)
    print("Validation: accuracy = %.6f loss = %.6f" % (acc, loss))
    if 'val_acc' in h.history:
        print("Over fitting score   = %.6f" % over_fitting_score(h))
        print("Under fitting score  = %.6f" % under_fitting_score(h))
    print("Params count:", model.count_params())
    print("stop epoch =", max(h.epoch))
    print("epochs =", h.params['epochs'])
    print("batch_size =", h.params['batch_size'])
    print("samples =", h.params['samples'])
    #view_acc(h)
    id = model.name[-1]
    #plt.savefig(model.name + '_acc_graph.png')
    #plt.show()
    view_loss(h)
    plt.savefig(model.name + '_loss_graph.png')
    plt.show()

def view_acc(h):
    # Accuracy history graph
    plt.plot(h.history['acc'])
    if 'val_acc' in h.history:
        plt.plot(h.history['val_acc'])
    plt.title('model accuracy')
    plt.ylabel('accuracy')
    plt.xlabel('epoch')
    leg = plt.legend(['train', 'validation'], loc='best')
    plt.setp(leg.get_lines(), linewidth=3.0)

def view_loss(h):
    # Loss history graph
    plt.plot(h.history['loss'])
    if 'val_loss' in h.history:
        plt.plot(h.history['val_loss'])
    plt.title('model loss')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    leg = plt.legend(['train', 'validation'], loc='best')
    plt.setp(leg.get_lines(), linewidth=3.0)

# http://machinelearningmastery.com/improve-deep-learning-performance
def over_fitting_score(h):
    gap = []
    n = len(h.epoch)
    for i in h.epoch:
        acc = h.history['acc'][i]
        val_acc = h.history['val_acc'][i]
        # late gaps get higher weight ..
        gap.append( i * abs(acc-val_acc))
    ofs = sum(gap) / (n * (n-1) / 2)
    return ofs

def under_fitting_score(h):
    gap = []
    for i in h.epoch:
        acc = h.history['acc'][i]
        val_acc = h.history['val_acc'][i]
        gap.append(abs(acc-val_acc))
    gap = np.array(gap)
    return gap.mean()

def find_best_epoch(h, thresh=0.02):
    epochs = []
    for i in h.epoch:
        loss = h.history['loss'][i]
        val_loss = h.history['val_loss'][i]
        if abs(loss-val_loss) <= thresh:
            epochs.append(i)

    if not epochs:
        print("No result")
        return None
    max_e = -1
    max_val_loss = -1
    for i in epochs:
        if h.history['val_loss'][i] > max_val_loss:
            max_e = i
            max_val_loss = h.history['val_loss'][i]
    print("best epoch = %d ; best loss = %.6f ; best val_loss = %.6f" % (max_e, h.history['loss'][max_e], h.history['val_loss'][max_e]))
    return max_e

def success_rate(model, X_test, y_test):
    y_pred = model.predict_classes(X_test)
    n = len(y_pred)
    s = 0
    for i in range(n):
        if y_pred[i] == y_test[i]:
            s += 1
    return float(s) / n

def save_model_summary(model, filename):
    current_stdout = sys.stdout
    f = open(filename, 'w')
    sys.stdout = f
    model.summary()
    sys.stdout = current_stdout
    f.close()
    return filename

del imgutils
del dlutils
