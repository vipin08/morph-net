"""A NetworkRegularizer that targets the number of weights in the model."""

from __future__ import absolute_import
from __future__ import division
# [internal] enable type annotations
from __future__ import print_function

from morph_net.framework import batch_norm_source_op_handler
from morph_net.framework import generic_regularizers
from morph_net.framework import op_handler_decorator
from morph_net.framework import op_handlers
from morph_net.framework import op_regularizer_manager as orm
from morph_net.network_regularizers import cost_calculator
from morph_net.network_regularizers import resource_function
from typing import Type


class GammaModelSizeRegularizer(generic_regularizers.NetworkRegularizer):
  """A NetworkRegularizer that targets model size using Gamma L1."""

  def __init__(
      self,
      ops,
      gamma_threshold,
      regularizer_decorator: Type[generic_regularizers.OpRegularizer] = None,
      decorator_parameters=None,
      inputs=None,
      force_group=None,
      regularizer_blacklist=None):
    """Creates a GammaModelSizeRegularizer object.

    Args:
      ops: A list of tf.Operation. An OpRegularizer will be created for all
        the ops in `ops`, and recursively for all ops they depend on via data
        dependency. Typically `ops` would contain a single tf.Operation, which
        is the output of the network.
      gamma_threshold: A float scalar, will be used as a 'gamma_threshold' for
        all instances GammaL1Regularizer created by this class.
      regularizer_decorator: A string, the name of the regularizer decorators
        to use. Supported decorators are listed in
        op_regularizer_decorator.SUPPORTED_DECORATORS.
      decorator_parameters: A dictionary of parameters to pass to the decorator
        factory. To be used only with decorators that requires parameters,
        otherwise use None.
      inputs: List of regex for ops that should terminate graph traversal.
      force_group: List of regex for ops that should be force-grouped.  Each
        regex corresponds to a separate group.  Use '|' operator to specify
        multiple patterns in a single regex. See op_regularizer_manager for
        more detail.
      regularizer_blacklist: List of regex for ops that should not be
        regularized. See op_regularizer_manager for more detail.
    """
    source_op_handler = batch_norm_source_op_handler.BatchNormSourceOpHandler(
        gamma_threshold)
    if regularizer_decorator:
      source_op_handler = op_handler_decorator.OpHandlerDecorator(
          source_op_handler, regularizer_decorator, decorator_parameters)
    op_handler_dict = op_handlers.get_gamma_op_handler_dict()
    op_handler_dict.update({
        'FusedBatchNorm': source_op_handler,
        'FusedBatchNormV2': source_op_handler,
    })

    self._manager = orm.OpRegularizerManager(
        ops, op_handler_dict, inputs=inputs,
        force_group=force_group, regularizer_blacklist=regularizer_blacklist)
    self._calculator = cost_calculator.CostCalculator(
        self._manager, resource_function.model_size_function)

  def get_regularization_term(self, ops=None):
    return self._calculator.get_regularization_term(ops)

  def get_cost(self, ops=None):
    return self._calculator.get_cost(ops)

  @property
  def op_regularizer_manager(self):
    return self._manager

  @property
  def name(self):
    return 'ModelSizeV2'

  @property
  def cost_name(self):
    return 'ModelSize'
