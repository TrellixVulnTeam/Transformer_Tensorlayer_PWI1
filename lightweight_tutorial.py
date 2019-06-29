#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import unittest

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import tensorflow as tf
import tensorlayer as tl
import numpy as np
import argparse
from utils.tokenizer import *
from weightLightModels.transformer import Transformer
from weightLightModels import models_params 
from utils.pipeline_dataset import train_input_fn
from utils import metrics
from models import optimizer


class CustomSchedule(tf.keras.optimizers.schedules.LearningRateSchedule):
  def __init__(self, d_model, warmup_steps=5):
    super(CustomSchedule, self).__init__()
    
    self.d_model = d_model
    self.d_model = tf.cast(self.d_model, tf.float32)

    self.warmup_steps = warmup_steps
    
  def __call__(self, step):
    arg1 = tf.math.rsqrt(step)
    arg2 = step * (self.warmup_steps ** -1.5)
    
    return tf.math.rsqrt(self.d_model) * tf.math.minimum(arg1, arg2)




def train_model(input_params):
    params = model_params.EXAMPLE_PARAMS
    dataset = train_input_fn(input_params)
    
    num_epochs = 50
    # @tf.function
    
    def train_step(inputs, targets):
        
        with tf.GradientTape() as tape:
            #print(inputs)
            
            logits = model(inputs=inputs, targets=targets)
            logits = metrics.MetricLayer(params.vocab_size)([logits, targets])
            logits, loss = metrics.LossLayer(params.vocab_size, 0.1)([logits, targets])

            
        gradients = tape.gradient(loss, model.all_weights)
        optimizer_.apply_gradients(zip(gradients, model.all_weights))
        return loss

    
    model = Transformer(params)
    model.train()
    learning_rate = CustomSchedule(params.hidden_size, warmup_steps=params.learning_rate_warmup_steps)
    optimizer_ = optimizer.LazyAdam(learning_rate, beta_1=0.9, beta_2=0.98, epsilon=1e-9)
    
    
    for epoch in range(num_epochs):
        total_loss, n_iter = 0, 0
        for i, [inputs, targets] in enumerate(dataset):
            loss = train_step(inputs, targets)
            if (i % 100 == 0):
                print('Batch ID {} at Epoch [{}/{}]: loss {:.4f}'.format(i, epoch + 1, num_epochs, loss))
            if ((i+1) % 2000 == 0):
                tl.files.save_npz(model.all_weights, name='./checkouts_tl/model.npz')
            total_loss += loss
            n_iter += 1

        # printing average loss after every epoch
        print('Epoch [{}/{}]: loss {:.4f}'.format(epoch + 1, num_epochs, total_loss / n_iter))
        tl.files.save_npz(model.all_weights, name='./checkouts_tl/model.npz')





if __name__ == '__main__':

    params = {}
    params["batch_size"] = 2048
    params["max_length"] = 256
    params["num_parallel_calls"] = 1
    params["repeat_dataset"] = 1
    params["static_batch"] = False
    params["num_gpus"] = 1
    params["use_synthetic_data"] = False
    params["data_dir"] = './data/data/wmt32k-train*'
    train_model(params)