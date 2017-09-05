import os
os.environ['KERAS_BACKEND'] = 'theano'
from data import load_preprocessed_data
from keras import backend as K
from keras import initializers
from keras.engine.topology import Layer, InputSpec
from keras.layers import activations, Wrapper, Recurrent
from keras.layers import LSTM, Bidirectional, Dense
from keras.layers import Embedding, Input, Dropout
from keras.models import Model


INPUT_DIM = 22000
SENT_LEN = 100
EMBD_DIM = 128


class AttLayer(Layer):
    def __init__(self, **kwargs):
        self.init = initializers.get('normal')
        super(AttLayer, self).__init__(** kwargs)

    def build(self, input_shape):
        assert len(input_shape) == 3
        self.W = K.variable(self.init((input_shape[-1],)))
        self.trainable_weights = [self.W]
        super(AttLayer, self).build(input_shape)

    def call(self, x, mask=None):
        eij = K.tanh(K.dot(x, self.W))

        ai = K.exp(eij)
        weights = ai / K.sum(ai, axis=1).dimshuffle(0, 'x')

        weighted_input = x * weights.dimshuffle(0, 1, 'x')
        return weighted_input.sum(axis=1)

    def compute_output_shape(self, input_shape):
        return (input_shape[0], input_shape[-1])


if __name__ == "__main__":
    inputs_, outputs_ = load_preprocessed_data()

    inputs = Input(shape=(SENT_LEN,), dtype="int32")
    embeddings = Embedding(input_dim=INPUT_DIM, output_dim=EMBD_DIM,
                           input_length=SENT_LEN)(inputs)
    lstm1 = Bidirectional(LSTM(units=64, return_sequences=True))(embeddings)
    attention = AttLayer()(lstm1)
    # dropout = Dropout(0.35)(lstm1)
    outputs = Dense(1, activation="sigmoid")(attention)

    model = Model(inputs=inputs, outputs=outputs)
    model.summary()

    model.compile(loss="binary_crossentropy", optimizer="adam",
                  metrics=["accuracy"])
    model.fit(x=inputs_, y=outputs_, validation_split=0.20, batch_size=64,
              epochs=3)
