# set seeds for reproducibility of results
from numpy.random import seed
seed(42)
from tensorflow import set_random_seed
set_random_seed(42)

# classical imports
import numpy as np
import os
import chess
import time
from keras.models import Sequential
from keras.layers import Dense, Activation, Conv2D, Flatten, BatchNormalization, Dropout
from keras.utils import plot_model
from keras.callbacks import EarlyStopping
from keras.optimizers import Adam
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

## FUNCTIONS
def array_to_single(array):
    single = []
    for arr in array:
        val = 0
        for pos in range(0, len(arr)):
            if pos > val:
                val = arr[pos]
                max_pos = pos+1
        single.append(max_pos)
    return single

def cp_to_p(cp):
    return 1/(1+10**(-cp/4))

def p_to_cp(p):
    if p != 1:
        return 4*np.log10(p/(1-p))
    else:
        return 128

def fen_to_colors_input(fen):
    board = chess.Board(fen)
    input = np.zeros((8,8,3), dtype=int)

    for i in range(0,64):
        if board.piece_at(i) == chess.Piece(chess.PAWN, chess.WHITE):
            input[i//8,i%8,0] = 1
        elif board.piece_at(i) == chess.Piece(chess.PAWN, chess.BLACK):
            input[i//8,i%8,1] = -1
        elif board.piece_at(i) == chess.Piece(chess.KNIGHT, chess.WHITE):
            input[i//8,i%8,0] = 2
        elif board.piece_at(i) == chess.Piece(chess.KNIGHT, chess.BLACK):
            input[i//8,i%8,1] = -2
        elif board.piece_at(i) == chess.Piece(chess.BISHOP, chess.WHITE):
            input[i//8,i%8,0] = 3
        elif board.piece_at(i) == chess.Piece(chess.BISHOP, chess.BLACK):
            input[i//8,i%8,1] = -3
        elif board.piece_at(i) == chess.Piece(chess.ROOK, chess.WHITE):
            input[i//8,i%8,0] = 4
        elif board.piece_at(i) == chess.Piece(chess.ROOK, chess.BLACK):
            input[i//8,i%8,1] = -4
        elif board.piece_at(i) == chess.Piece(chess.QUEEN, chess.WHITE):
            input[i//8,i%8,0] = 5
        elif board.piece_at(i) == chess.Piece(chess.QUEEN, chess.BLACK):
            input[i//8,i%8,1] = -5
        elif board.piece_at(i) == chess.Piece(chess.KING, chess.WHITE):
            input[i//8,i%8,0] = 6
        elif board.piece_at(i) == chess.Piece(chess.KING, chess.BLACK):
            input[i//8,i%8,1] = -6
        if not board.turn:
            input[i//8,i%8,2] = -1
    
    return input

def fen_to_pieces_input(fen):
    board = chess.Board(fen)
    input = np.zeros((8,8,7), dtype=int)

    for i in range(0,64):
        if board.piece_at(i) == chess.Piece(chess.PAWN, chess.WHITE):
            input[i//8,i%8,0] = 1
        elif board.piece_at(i) == chess.Piece(chess.PAWN, chess.BLACK):
            input[i//8,i%8,0] = -1
        elif board.piece_at(i) == chess.Piece(chess.KNIGHT, chess.WHITE):
            input[i//8,i%8,1] = 1
        elif board.piece_at(i) == chess.Piece(chess.KNIGHT, chess.BLACK):
            input[i//8,i%8,1] = -1
        elif board.piece_at(i) == chess.Piece(chess.BISHOP, chess.WHITE):
            input[i//8,i%8,2] = 1
        elif board.piece_at(i) == chess.Piece(chess.BISHOP, chess.BLACK):
            input[i//8,i%8,2] = -1
        elif board.piece_at(i) == chess.Piece(chess.ROOK, chess.WHITE):
            input[i//8,i%8,3] = 1
        elif board.piece_at(i) == chess.Piece(chess.ROOK, chess.BLACK):
            input[i//8,i%8,3] = -1
        elif board.piece_at(i) == chess.Piece(chess.QUEEN, chess.WHITE):
            input[i//8,i%8,4] = 1
        elif board.piece_at(i) == chess.Piece(chess.QUEEN, chess.BLACK):
            input[i//8,i%8,4] = -1
        elif board.piece_at(i) == chess.Piece(chess.KING, chess.WHITE):
            input[i//8,i%8,5] = 1
        elif board.piece_at(i) == chess.Piece(chess.KING, chess.BLACK):
            input[i//8,i%8,5] = -1
        if not board.turn:
            input[i//8,i%8,6] = -1
        else:
            input[i//8,i%8,6] = 1
    
    return input

def fen_to_just_pieces_input(fen):
    board = chess.Board(fen)
    input = np.zeros((8,8,7), dtype=int)

    for i in range(0,64):
        if board.piece_at(i) == chess.Piece(chess.PAWN, chess.WHITE):
            input[i//8,i%8,0] = 1
        elif board.piece_at(i) == chess.Piece(chess.PAWN, chess.BLACK):
            input[i//8,i%8,0] = -1
        elif board.piece_at(i) == chess.Piece(chess.KNIGHT, chess.WHITE):
            input[i//8,i%8,1] = 1
        elif board.piece_at(i) == chess.Piece(chess.KNIGHT, chess.BLACK):
            input[i//8,i%8,1] = -1
        elif board.piece_at(i) == chess.Piece(chess.BISHOP, chess.WHITE):
            input[i//8,i%8,2] = 1
        elif board.piece_at(i) == chess.Piece(chess.BISHOP, chess.BLACK):
            input[i//8,i%8,2] = -1
        elif board.piece_at(i) == chess.Piece(chess.ROOK, chess.WHITE):
            input[i//8,i%8,3] = 1
        elif board.piece_at(i) == chess.Piece(chess.ROOK, chess.BLACK):
            input[i//8,i%8,3] = -1
        elif board.piece_at(i) == chess.Piece(chess.QUEEN, chess.WHITE):
            input[i//8,i%8,4] = 1
        elif board.piece_at(i) == chess.Piece(chess.QUEEN, chess.BLACK):
            input[i//8,i%8,4] = -1
        elif board.piece_at(i) == chess.Piece(chess.KING, chess.WHITE):
            input[i//8,i%8,5] = 1
        elif board.piece_at(i) == chess.Piece(chess.KING, chess.BLACK):
            input[i//8,i%8,5] = -1
        if not board.turn:
            input[i//8,i%8,6] = -1
        else:
            input[i//8,i%8,6] = 1
    
    return input

def eval_to_7_class(eval):
    # create data for evaluation into 7 groups
    # +-100     -> 3 -> draw
    # 100-300   -> 2,4
    # 300-600   -> 1,5
    # 600+      -> 0,6 -> won

    output = np.zeros(7, dtype=float)
    # draw
    if eval <= 100 and eval >= -100:
        output[3] = 1
    #better for white
    elif eval > 100 and  eval <= 300:
        output[4] = 1
    elif eval > 300 and eval <= 600:
        output[5] = 1
    elif eval > 600:
        output[6] = 1
    # better for black
    elif eval < -100 and  eval >= -300:
        output[2] = 1
    elif eval < -300 and eval >= -600:
        output[1] = 1
    elif eval < -600:
        output[0] = 1
    
    return output

def eval_to_sparse_7_class(eval):
    # create data for evaluation into 7 groups
    # +-100     -> 3 -> draw
    # 100-300   -> 2,4
    # 300-600   -> 1,5
    # 600+      -> 0,6 -> won

    # draw
    if eval <= 100 and eval >= -100:
        output = 3
    #better for white
    elif eval > 100 and  eval <= 300:
        output = 4
    elif eval > 300 and eval <= 600:
        output = 5
    elif eval > 600:
        output = 6
    # better for black
    elif eval < -100 and  eval >= -300:
        output = 2
    elif eval < -300 and eval >= -600:
        output = 1
    elif eval < -600:
        output = 0
    
    return output

def eval_to_13_class(eval):
    # create data for evaluation into 13 groups
    # +-50      -> 6 -> draw
    # 50-100    -> 5,7
    # 100-200   -> 4,8
    # 200-300   -> 3,9
    # 300-400   -> 2,10
    # 400-600   -> 1,11
    # 600+      -> 0,12


    output = np.zeros(13, dtype=float)
    # draw
    if eval <= 50 and eval >= -50:
        output[6] = 1
    #better for white
    elif eval > 50 and  eval <= 100:
        output[7] = 1
    elif eval > 100 and eval <= 200:
        output[8] = 1
    elif eval > 200 and  eval <= 300:
        output[9] = 1
    elif eval > 300 and  eval <= 400:
        output[10] = 1
    elif eval > 400 and eval <= 600:
        output[11] = 1
    elif eval > 600:
        output[12] = 1
    # better for black
    elif eval < -50 and  eval >= -100:
        output[5] = 1
    elif eval < -100 and eval >= -200:
        output[4] = 1
    elif eval < -200 and  eval >= -300:
        output[3] = 1
    elif eval < -300 and  eval >= -400:
        output[2] = 1
    elif eval < -400 and eval >= -600:
        output[1] = 1
    elif eval < -600:
        output[0] = 1
    
    return output

def eval_to_25_class(eval):
    ## create data for evaluation into 7 groups
    # +- 20     -> group 12 - draw
    # 20 - 40   -> group 11,13
    # 40 - 60   -> group 10,14
    # 60 - 80   -> group 9,15
    # 80 - 100  -> group 8,16
    # 100 - 150 -> group 7,17
    # 150 - 200 -> group 6,18
    # 200 - 250 -> group 5,19
    # 250 - 300 -> group 4,20
    # 300 - 350 -> group 3,21
    # 350 - 400 -> group 2,22
    # 400 - 500 -> group 1,23
    # 500+      -> group 0,24 - win

    output = np.zeros(25, dtype=float)
    # draw
    if eval <= 20 and eval >= -20:
        output[12] = 1
    #better for white
    elif eval > 20 and eval <= 40:
        output[13] = 1
    elif eval > 40 and eval <= 60:
        output[14] = 1
    elif eval > 60 and eval <= 80:
        output[15] = 1
    elif eval > 80 and eval <= 100:
        output[16] = 1
    elif eval > 100 and eval <= 150:
        output[17] = 1
    elif eval > 150 and eval <= 200:
        output[18] = 1
    elif eval > 200 and eval <= 250:
        output[19] = 1
    elif eval > 250 and eval <= 300:
        output[20] = 1
    elif eval > 300 and eval <= 350:
        output[21] = 1
    elif eval > 350 and eval <= 400:
        output[22] = 1
    elif eval > 400 and eval <= 500:
        output[23] = 1
    elif eval > 500:
        output[24] = 1
    # better for black
    elif eval < -20 and eval >= -40:
        output[11] = 1
    elif eval < -40 and eval >= -60:
        output[10] = 1
    elif eval < -60 and eval >= -80:
        output[9] = 1
    elif eval < -80 and eval >= -100:
        output[8] = 1
    elif eval < -100 and eval >= -150:
        output[7] = 1
    elif eval < -150 and eval >= -200:
        output[6] = 1
    elif eval < -200 and eval >= -250:
        output[5] = 1
    elif eval < -250 and eval >= -300:
        output[4] = 1
    elif eval < -300 and eval >= -350:
        output[3] = 1
    elif eval < -350 and eval >= -400:
        output[2] = 1
    elif eval < -400 and eval >= -500:
        output[1] = 1
    elif eval < -500:
        output[0] = 1
    
    return output

def load_data(input_type='colors', output_type='class'):
    ## input_type = 'colors' or 'pieces'
    ## output_type = 'class' or 'single'

    # load fen positions
    start = time.time()
    print('\nLoading positions')
    # positions = open('C:/Users/maelic/Documents/VUT/DP/nn_backend/games1.txt', "r")
    positions = open('C:/Users/maelic/Documents/VUT/DP/nn_backend/games7.txt', "r")
    fens = positions.read().split('\n')
    positions.close()
    print('Positions loaded in', int(time.time()-start),'seconds\n')

    # load evaluations
    start = time.time()
    print('Loading evaluations')
    # evals = open('C:/Users/maelic/Documents/VUT/DP//nn_backend/games1_eval_depth10.txt', "r")
    evals = open('C:/Users/maelic/Documents/VUT/DP//nn_backend/games7_eval.txt', "r")
    evaluations = evals.read().split('\n')
    evals.close()
    print('Evaluations loaded in', int(time.time()-start),'seconds\n')

    # prepare input data
    start = time.time()
    print('Preparing input')
    x = []
    if input_type == 'colors':
        for i in range(0,len(fens)):
            x.append(fen_to_colors_input(fens[i]))
    elif input_type == 'pieces':
        for i in range(0,len(fens)):
            x.append(fen_to_pieces_input(fens[i]))
    x = np.array(x)
    print('Input prepared in', int(time.time()-start),'seconds\n')

    # prepare output data
    start = time.time()
    print('Preparing output')
    y = []
    if output_type == 'single':
        for i in range(0,len(evaluations)):
            try:
                y.append(float(evaluations[i])/600)
            except:
                break
    elif output_type == 'class':
        for i in range(0,len(evaluations)):
            try:
                y.append(eval_to_sparse_7_class(float(evaluations[i])))
            except:
                break
    y = np.array(y)
    print('Output prepared in', int(time.time()-start),'seconds\n')

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)    
    return x_train, x_test, y_train, y_test

def model_1(x_train, y_train, x_test, y_test):
    ## MODEL 1, regression
    model = Sequential()

    model.add(Dense(448, input_shape=x_train[0].shape))
    model.add(Flatten())

    model.add(Dense(256))
    model.add(BatchNormalization())
    model.add(Activation('relu'))
    model.add(Dropout(0.2))

    model.add(Dense(64))
    model.add(BatchNormalization())
    model.add(Activation('relu'))
    model.add(Dropout(0.2))

    model.add(Dense(16))
    model.add(BatchNormalization())
    model.add(Activation('relu'))
    model.add(Dropout(0.2))

    model.add(Dense(1))
    
    adam = Adam(lr=0.00001)
    model.compile(
        loss='mean_squared_error',
        optimizer=adam,
        metrics=['acc']
    )
    es = EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=16)

    history = model.fit(
        x_train,
        y_train,
        batch_size=128,
        epochs=256,
        validation_data=(x_test, y_test),
        callbacks=[es]
    )

    return model, history

def model_2(x_train, y_train, x_test, y_test):
    ## MODEL 2 - classification
    model = Sequential()
    model.add(Conv2D(512, kernel_size=5, input_shape=x_train[0].shape))
    model.add(BatchNormalization())
    model.add(Activation('relu'))

    model.add(Conv2D(1024, kernel_size=3))
    model.add(BatchNormalization())
    model.add(Activation('relu'))

    model.add(Flatten())

    model.add(Dense(1024))
    model.add(Activation('relu'))
    model.add(Dropout(0.5))

    model.add(Dense(256))
    model.add(Activation('relu'))
    model.add(Dropout(0.5))
    
    model.add(Dense(64))
    model.add(Activation('relu'))
    model.add(Dropout(0.5))

    model.add(Dense(13))
    model.add(Activation('softmax'))

    model.compile(
        loss='sparse_categorical_crossentropy',
        optimizer="sgd",
        metrics=['sparse_categorical_accuracy']
    )
    es = EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=16)

    history = model.fit(
        x_train,
        y_train,
        batch_size=32,
        epochs=128,
        validation_data=(x_test, y_test),
        callbacks=[es]
    )

    return model, history

def model_3(x_train, y_train, x_test, y_test):
    ## MODEL 3 - classification
    model = Sequential()
    model.add(Conv2D(256, kernel_size=3, input_shape=x_train[0].shape))
    model.add(BatchNormalization())
    model.add(Activation('relu'))

    model.add(Conv2D(512, kernel_size=3))
    model.add(BatchNormalization())
    model.add(Activation('relu'))

    model.add(Flatten())
    
    model.add(Dense(512))
    model.add(Activation('relu'))
    model.add(Dropout(0.3))

    model.add(Dense(7))
    model.add(Activation('softmax'))

    adam = Adam(lr=0.00001)
    model.compile(
        loss='sparse_categorical_crossentropy',
        optimizer=adam,
        metrics=['sparse_categorical_accuracy']
    )
    es = EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=8)

    history = model.fit(
        x_train,
        y_train,
        batch_size=256,
        epochs=128,
        validation_data=(x_test, y_test),
        callbacks=[es]
    )

    return model, history

def model_4(x_train, y_train, x_test, y_test):
    ## MODEL 4 - regression
    model = Sequential()
    model.add(Conv2D(128, kernel_size=3, input_shape=x_train[0].shape))
    model.add(BatchNormalization())
    model.add(Activation('relu'))

    model.add(Conv2D(256, kernel_size=3))
    model.add(BatchNormalization())
    model.add(Activation('relu'))

    model.add(Flatten())
    
    model.add(Dense(256))
    model.add(Activation('relu'))
    model.add(Dropout(0.5))

    model.add(Dense(1))

    adam = Adam(lr=0.0001)
    model.compile(
        loss='mse',
        optimizer=adam,
        metrics=['acc']#, 'mae', 'mape', 'cosine']
    )
    es = EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=8)

    history = model.fit(
        x_train,
        y_train,
        batch_size=256,
        epochs=128,
        validation_data=(x_test, y_test),
        callbacks=[es]
    )

    return model, history

def model_5(x_train, y_train, x_test, y_test):
    ## MODEL 5 - regression
    model = Sequential()
    model.add(Dense(256, input_shape=x_train[0].shape))
    model.add(BatchNormalization())
    model.add(Activation('relu'))
    model.add(Dropout(0.3))
    model.add(Flatten())
    
    model.add(Dense(128))
    model.add(BatchNormalization())
    model.add(Activation('relu'))
    model.add(Dropout(0.3))

    model.add(Dense(32))
    model.add(BatchNormalization())
    model.add(Activation('relu'))
    model.add(Dropout(0.3))

    model.add(Dense(1))

    adam = Adam(lr=0.0001)
    model.compile(
        loss='mse',
        optimizer=adam,
        metrics=['acc']
    )
    es = EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=16)

    history = model.fit(
        x_train,
        y_train,
        batch_size=256,
        epochs=128,
        validation_data=(x_test, y_test),
        callbacks=[es]
    )

    return model, history

def eval_model(model, x_test, y_test, save):
    # Test model and print score
    if save[0]:
        model.save(save[1])
    score, acc = model.evaluate(x_test, y_test, batch_size=128)
    print('\nTest score:', score)
    print('Test accuracy:', acc)    

def load_npy_data(type, depth):
    # type -> single/class, depth -> 5/10
    x = np.load('C:/Users/maelic/Documents/VUT/DP/nn_backend/npy_data_50k/input.npy')
    if type == 'single' and depth == 5:        
        y = np.load('C:/Users/maelic/Documents/VUT/DP/nn_backend/npy_data_50k/single_output_d5.npy')
    elif type == 'single' and depth == 10:
        y = np.load('C:/Users/maelic/Documents/VUT/DP/nn_backend/npy_data_50k/single_output_d10.npy')
    elif type == 'class' and depth == 5:
        y = np.load('C:/Users/maelic/Documents/VUT/DP/nn_backend/npy_data_50k/class_output_d5.npy')
    elif type == 'class' and depth == 10:
        y = np.load('C:/Users/maelic/Documents/VUT/DP/nn_backend/npy_data_50k/class_output_d10.npy')

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)
    return x_train, x_test, y_train, y_test

## MAIN
if __name__ == '__main__':
    # load data
    print('Loading data..')
    x_train, x_test, y_train, y_test = load_npy_data('single', 10)

    # create model
    print('Creating model..')
    model, history = model_5(x_train, y_train, x_test, y_test)
    # plot_model(model, to_file='model.png')

    # test (and save) model
    print('Saving and testing..')
    save = [True, 'C:/Users/maelic/Documents/VUT/DP/nn_backend/models/model5_50k_1.h5']
    eval_model(model, x_test, y_test, save)

    # visualization (False for regression, True for classification)
    print('Visualization..')
    if False:
        plt.plot(history.history['sparse_categorical_accuracy'])
        plt.plot(history.history['val_sparse_categorical_accuracy'])
        plt.title('Model accuracy')
        plt.ylabel('Cathegorical accuracy')
        plt.xlabel('Epoch')
        plt.legend(['Train', 'Test'], loc='upper left')
        plt.show()

        plt.plot(history.history['loss'])
        plt.plot(history.history['val_loss'])
        plt.title('Model loss')
        plt.ylabel('Loss')
        plt.xlabel('Epoch')
        plt.legend(['Train', 'Test'], loc='upper left')
        plt.show()
    else:
        plt.plot(history.history['acc'])
        plt.plot(history.history['val_acc'])
        plt.title('Model accuracy')
        plt.ylabel('Accuracy')
        plt.xlabel('Epoch')
        plt.legend(['Train', 'Test'], loc='upper left')
        plt.show()

        plt.plot(history.history['loss'])
        plt.plot(history.history['val_loss'])
        plt.title('Model loss')
        plt.ylabel('Loss')
        plt.xlabel('Epoch')
        plt.legend(['Train', 'Test'], loc='upper left')
        plt.show()

        # plt.plot(history.history['mean_absolute_error'])
        # plt.plot(history.history['val_mean_absolute_error'])
        # plt.title('Model metric MEA')
        # plt.ylabel('Loss')
        # plt.xlabel('Epoch')
        # plt.legend(['Train', 'Test'], loc='upper left')
        # plt.show()

        # plt.plot(history.history['mean_absolute_percentage_error'])
        # plt.plot(history.history['val_mean_absolute_percentage_error'])
        # plt.title('Model metric MAPE')
        # plt.ylabel('Loss')
        # plt.xlabel('Epoch')
        # plt.legend(['Train', 'Test'], loc='upper left')
        # plt.show()

        # plt.plot(history.history['cosine_proximity'])
        # plt.plot(history.history['val_cosine_proximity'])
        # plt.title('Model cosine proximity')
        # plt.ylabel('Loss')
        # plt.xlabel('Epoch')
        # plt.legend(['Train', 'Test'], loc='upper left')
        # plt.show()