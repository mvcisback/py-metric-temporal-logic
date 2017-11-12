from stl import pointwise_sat


def ordered_evaluator(phi):
    params = {ap.name for ap in phi.params}
    order = tuple(params)

    def vec_to_dict(theta):
        return {k: v for k, v in zip(order, theta)}

    def eval_phi(theta, x):
        return pointwise_sat(phi.set_params(vec_to_dict(theta)))(x, 0)

    return eval_phi, order
