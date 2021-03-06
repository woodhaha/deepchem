from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

__author__ = "Joseph Gomes"
__copyright__ = "Copyright 2017, Stanford University"
__license__ = "MIT"

import os
import sys
import deepchem as dc
import numpy as np
import tensorflow as tf

sys.path.append("../../models")
from atomicnet_ops import create_symmetry_parameters
from atomicnet import TensorflowFragmentRegressor

seed = 123
np.random.seed(seed)
tf.set_random_seed(seed)

base_dir = os.getcwd()
data_dir = os.path.join(base_dir, "datasets")
train_dir = os.path.join(data_dir, "scaffold_train")
test_dir = os.path.join(data_dir, "scaffold_test")
model_dir = os.path.join(base_dir, "scaffold_model")

frag1_num_atoms = 140
frag2_num_atoms = 821
complex_num_atoms = 908
max_num_neighbors = 12
neighbor_cutoff = 12.0

train_dataset = dc.data.DiskDataset(train_dir)
test_dataset = dc.data.DiskDataset(test_dir)
pdbbind_tasks = ["-logKd/Ki"]
transformers = [
    dc.trans.NormalizationTransformer(transform_y=True, dataset=train_dataset)
]
for transformer in transformers:
  train_dataset = transformer.transform(train_dataset)
  test_dataset = transformer.transform(test_dataset)

at = [1., 6, 7., 8., 9., 11., 12., 15., 16., 17., 20., 25., 30., 35., 53.]
radial = [[12.0], [0.0, 4.0, 8.0], [4.0]]
rp = create_symmetry_parameters(radial)
layer_sizes = [32, 32, 16]
weight_init_stddevs = [
    1 / np.sqrt(layer_sizes[0]), 1 / np.sqrt(layer_sizes[1]),
    1 / np.sqrt(layer_sizes[2])
]
dropouts = [0., 0., 0.]
penalty_type = "l2"
penalty = 0.
model = TensorflowFragmentRegressor(
    len(pdbbind_tasks),
    rp,
    at,
    frag1_num_atoms,
    frag2_num_atoms,
    complex_num_atoms,
    max_num_neighbors,
    logdir=model_dir,
    layer_sizes=layer_sizes,
    weight_init_stddevs=weight_init_stddevs,
    bias_init_consts=[0., 0., 0.],
    penalty=penalty,
    penalty_type=penalty_type,
    dropouts=dropouts,
    learning_rate=0.002,
    momentum=0.8,
    optimizer="adam",
    batch_size=24,
    conv_layers=1,
    boxsize=None,
    verbose=True,
    seed=seed)
model.fit(train_dataset, nb_epoch=100)
metric = [
    dc.metrics.Metric(dc.metrics.mean_absolute_error, mode="regression"),
    dc.metrics.Metric(dc.metrics.pearson_r2_score, mode="regression")
]
train_evaluator = dc.utils.evaluate.Evaluator(model, train_dataset,
                                              transformers)
train_scores = train_evaluator.compute_model_performance(metric)
print("Train scores")
print(train_scores)
test_evaluator = dc.utils.evaluate.Evaluator(model, test_dataset, transformers)
test_scores = test_evaluator.compute_model_performance(metric)
print("Test scores")
print(test_scores)
