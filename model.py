import tensorflow as tf
import numpy as np
from Config import config
params = config()
class VGG_model(object):
    def __init__(self, inptut, output, keep_prob):
        self.X = inptut
        self.Y = output
        self.keep_prob = keep_prob

    def inference_op(self):
        # block 1 -- outputs 112x112x64
        conv1_1 = self.conv_op(self.X, name="conv1_1", kh=3, kw=3, n_out=64, dh=1, dw=1)
        conv1_2 = self.conv_op(conv1_1, name="conv1_2", kh=3, kw=3, n_out=64, dh=1, dw=1)
        pool1 = self.mpool_op(conv1_2, name="pool1", kh=2, kw=2, dw=2, dh=2)

        # block 2 -- outputs 56x56x128
        conv2_1 = self.conv_op(pool1, name="conv2_1", kh=3, kw=3, n_out=128, dh=1, dw=1)
        conv2_2 = self.conv_op(conv2_1, name="conv2_2", kh=3, kw=3, n_out=128, dh=1, dw=1)
        pool2 = self.mpool_op(conv2_2, name="pool2", kh=2, kw=2, dh=2, dw=2)

        # # block 3 -- outputs 28x28x256
        conv3_1 = self.conv_op(pool2, name="conv3_1", kh=3, kw=3, n_out=256, dh=1, dw=1)
        conv3_2 = self.conv_op(conv3_1, name="conv3_2", kh=3, kw=3, n_out=256, dh=1, dw=1)
        conv3_3 = self.conv_op(conv3_2, name="conv3_3", kh=3, kw=3, n_out=256, dh=1, dw=1)
        pool3 = self.mpool_op(conv3_3, name="pool3", kh=2, kw=2, dh=2, dw=2)

        # block 4 -- outputs 14x14x512
        conv4_1 = self.conv_op(pool3, name="conv4_1", kh=3, kw=3, n_out=512, dh=1, dw=1)
        conv4_2 = self.conv_op(conv4_1, name="conv4_2", kh=3, kw=3, n_out=512, dh=1, dw=1)
        conv4_3 = self.conv_op(conv4_2, name="conv4_3", kh=3, kw=3, n_out=512, dh=1, dw=1)
        pool4 = self.mpool_op(conv4_3, name="pool4", kh=2, kw=2, dh=2, dw=2)

        # block 5 -- outputs 7x7x512
        conv5_1 = self.conv_op(pool4, name="conv5_1", kh=3, kw=3, n_out=512, dh=1, dw=1)
        conv5_2 = self.conv_op(conv5_1, name="conv5_2", kh=3, kw=3, n_out=512, dh=1, dw=1)
        conv5_3 = self.conv_op(conv5_2, name="conv5_3", kh=3, kw=3, n_out=512, dh=1, dw=1)
        pool5 = self.mpool_op(conv5_3, name="pool5", kh=2, kw=2, dw=2, dh=2)

        # flatten
        shp = pool5.get_shape().as_list()
        flattened_shape = shp[1] * shp[2] * shp[3]
        resh1 = tf.reshape(pool5, [-1, flattened_shape], name="resh1")

        # fully connected
        fc6 = self.fc_op(resh1, name="fc6", n_out=4096)
        fc6_drop = tf.nn.dropout(fc6, self.keep_prob, name="fc6_drop")

        fc7 = self.fc_op(fc6_drop, name="fc7", n_out=4096)
        fc7_drop = tf.nn.dropout(fc7, self.keep_prob, name="fc7_drop")

        logits = self.fc_op(fc7_drop, name="fc8", n_out=4)
        return logits

    # 定义卷积操作
    def conv_op(self, input_op, name, kh, kw, n_out, dh, dw):
        input_op = tf.convert_to_tensor(input_op)
        n_in = input_op.get_shape()[-1].value
        with tf.name_scope(name) as scope:
            kernel = tf.get_variable(scope + "w",
                                     shape=[kh, kw, n_in, n_out],
                                     dtype=tf.float32,
                                     initializer=tf.contrib.layers.xavier_initializer_conv2d())
            conv = tf.nn.conv2d(input_op, kernel, (1, dh, dw, 1), padding='SAME')
            bias_init_val = tf.constant(0.0, shape=[n_out], dtype=tf.float32)
            biases = tf.Variable(bias_init_val, trainable=True, name='b')
            z = tf.nn.bias_add(conv, biases)
            activation = tf.nn.relu(z, name=scope)
            return activation

    # 定义全连接操作
    def fc_op(self, input_op, name, n_out):
        n_in = input_op.get_shape()[-1]
        with tf.name_scope(name) as scope:
            kernel = tf.get_variable(scope + 'w',
                                     shape=[n_in, n_out],
                                     dtype=tf.float32,
                                     initializer=tf.contrib.layers.xavier_initializer())
            biases = tf.Variable(tf.constant(0.1, shape=[n_out], dtype=tf.float32), name='b')
            # tf.nn.relu_layer对输入变量input_op与kernel做矩阵乘法加上bias，再做RELU非线性变换得到activation
            activation = tf.nn.relu_layer(input_op, kernel, biases, name=scope)
            return activation

    # 定义池化层
    def mpool_op(self, input_op, name, kh, kw, dh, dw):
        return tf.nn.max_pool(input_op,
                              ksize=[1, kh, kw, 1],
                              strides=[1, dh, dw, 1],
                              padding='SAME',
                              name=name)
    def load_original_weights(self, session, skip_layers=[]):
        weights = np.load('vgg16_weights.npz')
        keys = sorted(weights.keys())


        for i, name in enumerate(keys):
            parts = name.split('_')
            layer = '_'.join(parts[:-1])
            if layer == 'fc8':
                continue
            with tf.variable_scope(layer, reuse=True):
                if parts[-1] == 'W':
                    var = tf.get_variable('weights')
                    session.run(var.assign(weights[name]))
                elif parts[-1] == 'b':
                    var = tf.get_variable('biases')
                    session.run(var.assign(weights[name]))