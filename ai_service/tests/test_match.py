from src.face_engine import compare_embeddings


def vec(index):
    v = [0.0] * 512
    v[index] = 1.0
    return v


def test_correct_identity():
    output = compare_embeddings(vec(0), [
        {'user_id': 'sakha', 'embedding': vec(0)},
        {'user_id': 'barra', 'embedding': vec(1)},
    ])
    assert output['matched'] and output['user_id'] == 'sakha'


def test_unknown():
    output = compare_embeddings(vec(2), [
        {'user_id': 'sakha', 'embedding': vec(0)},
        {'user_id': 'barra', 'embedding': vec(1)},
    ])
    assert output['matched'] is False


def test_empty_gallery():
    assert not compare_embeddings(vec(0), [])['matched']


def test_duplicate_examples_per_user():
    output = compare_embeddings(vec(0), [
        {'user_id': 'sakha', 'embedding': vec(0)},
        {'user_id': 'sakha', 'embedding': vec(1)},
    ])
    assert output['matched'] and output['user_id'] == 'sakha'
