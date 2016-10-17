import os
import time
import mxnet as mx
import numpy as np
import cv2
import symbol
import cPickle as pickle
from matplotlib import pyplot as plt


def crop_img(im, size):
    im = cv2.imread(im)
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    if im.shape[0] > im.shape[1]:
        c = (im.shape[0]-im.shape[1]) / 2
        im = im[c:c+im.shape[1],:,:]
    else:
        c = (im.shape[1]-im.shape[0]) / 2
        im = im[:,c:c+im.shape[0],:]
    im = cv2.resize(im, size)
    return im

def preprocess_img(im, size):
    if type(size) == int:
        size = (size, size)
    im = crop_img(im, size)
    im = im.astype(np.float32)
    im = np.swapaxes(im, 0, 2)
    im = np.swapaxes(im, 1, 2)
    im[0,:] -= 123.68
    im[1,:] -= 116.779
    im[2,:] -= 103.939
    im = np.expand_dims(im, 0)
    return im

def postprocess_img(im):
    im = im[0]
    im[0,:] += 123.68
    im[1,:] += 116.779
    im[2,:] += 103.939
    im = np.swapaxes(im, 0, 2)
    im = np.swapaxes(im, 0, 1)
    im[im<0] = 0
    im[im>255] = 255
    return cv2.cvtColor(im.astype(np.uint8), cv2.COLOR_RGB2BGR)

class Maker():
    def __init__(self, model_prefix, output_shape):
        s0, s1 = output_shape
        s0 = s0//32*32
        s1 = s1//32*32
        self.s0 = s0
        self.s1 = s1
        generator = symbol.generator_symbol()
        args = mx.nd.load('%s_args.nd'%model_prefix)
        auxs = mx.nd.load('%s_auxs.nd'%model_prefix)
        args['data'] = mx.nd.zeros([1,3,s1,s0], mx.gpu())
        self.gene_executor = generator.bind(ctx=mx.gpu(), args=args, aux_states=auxs)

    def generate(self, save_path, content_path):
        self.gene_executor.arg_dict['data'][:] = preprocess_img(content_path, (self.s0, self.s1))
        self.gene_executor.forward(is_train=True)
        out = self.gene_executor.outputs[0].asnumpy()
        im = postprocess_img(out)
        cv2.imwrite(save_path, im)