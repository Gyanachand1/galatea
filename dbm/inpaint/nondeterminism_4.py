from pylearn2.config import yaml_parse
from galatea.dbm.inpaint.hack import OnMonitorError
import gc


def run(replay):
    yaml_src = """!obj:pylearn2.train.Train {
        dataset: &train !obj:pylearn2.datasets.binarizer.Binarizer {
            raw: &raw_train !obj:pylearn2.datasets.mnist.MNIST {
                which_set: "train",
                shuffle: 0,
                one_hot: 1,
                start: 0,
                stop: 50000
            }
        },
        model: !obj:galatea.dbm.inpaint.super_dbm.SuperDBM {
            batch_size : 1250,
            niter: 6, #note: since we have to backprop through the whole thing, this does
                      #increase the memory usage
            visible_layer: !obj:galatea.dbm.inpaint.super_dbm.BinaryVisLayer {
                nvis: 784,
                bias_from_marginals: *raw_train,
            },
            hidden_layers: [
                !obj:galatea.dbm.inpaint.super_dbm.DenseMaxPool {
                    detector_layer_dim: 500,
                            pool_size: 1,
                            sparse_init: 15,
                            layer_name: 'h0',
                            init_bias: 0.
                   },
                    !obj:galatea.dbm.inpaint.super_dbm.DenseMaxPool {
                            detector_layer_dim: 1000,
                            pool_size: 1,
                            sparse_init: 15,
                            layer_name: 'h1',
                            init_bias: 0.
                   },
                   !obj:galatea.dbm.inpaint.super_dbm.Softmax {
                            sparse_init: 15,
                            layer_name: 'c',
                            n_classes: 10
                   }
                  ]
        },
        algorithm: !obj:galatea.dbm.inpaint.inpaint_alg.InpaintAlgorithm {
                   theano_function_mode : !obj:pylearn2.devtools.record.RecordMode {
                            file_path: "nondetermism_4.txt",
                            replay: %d
                   },
                   monitoring_dataset : {
                            'train': *train,
                            'valid': !obj:pylearn2.datasets.binarizer.Binarizer { raw: !obj:pylearn2.datasets.mnist.MNIST {
                                    which_set: "train",
                                    shuffle: 0,
                                    one_hot: 1,
                                    start: 50000,
                                    stop: 60000
                                }},
                   },
                   line_search_mode: 'exhaustive',
                   init_alpha : [0.0256, .128, .256, 1.28, 2.56],
                   reset_alpha: 0,
                   conjugate: 1,
                   reset_conjugate: 0,
                   max_iter: 5,
                   cost: !obj:pylearn2.costs.cost.SumOfCosts {
                           costs :[
                                   !obj:galatea.dbm.inpaint.super_inpaint.SuperInpaint {
                                            both_directions : 0,
                                            noise : 0,
                                            supervised: 1,
                                            l1_act_targets: [  .06, .07, 0. ],
                                            l1_act_eps:     [  .04,  .05, 0. ],
                                            l1_act_coeffs:  [ .01,  .000, 0.  ]
                                   },
                                   !obj:galatea.dbm.inpaint.super_dbm.DBM_WeightDecay {
                                            coeffs: [ .0000005, .0000005, .0000005 ]
                                   }
                           ]
                   },
                   mask_gen : !obj:galatea.dbm.inpaint.super_inpaint.MaskGen {
                            drop_prob: 0.1,
                            balance: 0,
                            sync_channels: 0
                   }
            },
        extensions: [
                    !obj:galatea.dbm.inpaint.hack.ErrorOnMonitor {},
            ],
    }
    """
    train = yaml_parse.load(yaml_src % replay)

    try:
        train.main_loop()
        assert False # Should raise OnMonitorError
    except OnMonitorError:
        pass

    del train
    gc.collect()

run(0)
run(1)
