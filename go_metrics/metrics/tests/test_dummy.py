from twisted.trial.unittest import TestCase

from go_metrics.metrics.dummy import Fixtures, DummyMetrics, DummyBackend


class TestFixtures(TestCase):
    def test_add(self):
        fixtures = Fixtures()
        fixtures.add(foo='bar', result={'baz': 'quux'})
        self.assertEqual(fixtures.items, [{
            'foo': 'bar',
            'result': {'baz': 'quux'}
        }])

    def test_add_no_result(self):
        fixtures = Fixtures()
        fixtures.add(foo='bar')
        self.assertEqual(fixtures.items, [{
            'foo': 'bar',
            'result': {}
        }])

    def test_match(self):
        fixtures = Fixtures()
        fixtures.add(foo='bar', result={'baz': 'quux'})
        fixtures.add(corge='grault', result={'garply': 'waldo'})
        self.assertEqual(fixtures.match(foo='bar'), {'baz': 'quux'})
        self.assertEqual(fixtures.match(corge='grault'), {'garply': 'waldo'})
        self.assertEqual(fixtures.match(fred='xzyy'), {})


class TestDummyMetrics(TestCase):
    def test_get(self):
        backend = DummyBackend()
        metrics = DummyMetrics(backend, 'owner-1')
        backend.fixtures.add(foo='bar', result={'baz': 'quux'})
        self.assertEqual(metrics.get(foo='bar'), {'baz': 'quux'})


class TestDummyBackend(TestCase):
    pass
