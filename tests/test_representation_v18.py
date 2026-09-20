from pathlib import Path
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from wind_events.representation import gasf, polarity_bit, invert_gasf, Representation, SampledMedoids


def test_gasf_sign_symmetry_and_single_bit_inverse():
    x = np.random.default_rng(41).uniform(-1, 1, (50, 25))
    np.testing.assert_allclose(gasf(x), gasf(-x), atol=1e-12)
    np.testing.assert_allclose(invert_gasf(gasf(x), polarity_bit(x)), x, atol=1e-10)


def test_training_transform_is_frozen_and_bit_representation_has_six_dimensions():
    rng = np.random.default_rng(5)
    train, test = rng.uniform(-1, 1, (100, 25)), rng.uniform(-1, 1, (20, 25))
    for name in ("raw25", "raw_pca6", "gaf_pca6", "gaf_signed_pca6", "gaf_bit6"):
        model = Representation(name).fit(train)
        before = model.scaler.mean_.copy()
        result = model.transform(test)
        model.transform(-test)
        np.testing.assert_array_equal(before, model.scaler.mean_)
        assert result.shape == (20, 25 if name == "raw25" else 6)


def test_medoid_centers_are_actual_training_observations():
    x = np.random.default_rng(6).normal(size=(100, 4))
    model = SampledMedoids(4, 41, repetitions=2).fit(x)
    np.testing.assert_array_equal(model.cluster_centers_, x[model.medoid_indices_])
    assert model.predict(x).shape == (100,)


def test_nearest_prototype_margin_guarantees_assignment():
    centers = np.array([[0., 0.], [3., 0.], [0., 4.]])
    x = np.array([.3, .4])
    distance = np.linalg.norm(centers-x, axis=1)
    gap = np.sort(distance)[1]-distance.min()
    directions = np.random.default_rng(4).normal(size=(100, 2))
    directions /= np.linalg.norm(directions, axis=1)[:, None]
    perturbed = x+directions*gap*.49
    assert (np.linalg.norm(perturbed[:, None]-centers[None], axis=2).argmin(axis=1) == distance.argmin()).all()
