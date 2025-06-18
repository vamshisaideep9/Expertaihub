from django.test import TestCase

from .models import FAQQuestion, EMBED_DIM
from .utils import top5_related


class Top5RelatedTests(TestCase):
    def test_orders_by_distance_when_embeddings_present(self):
        q1 = FAQQuestion.objects.create(text="q1", embedding=[1.0] + [0.0]*(EMBED_DIM-1))
        q2 = FAQQuestion.objects.create(text="q2", embedding=[-1.0] + [0.0]*(EMBED_DIM-1))
        q3 = FAQQuestion.objects.create(text="q3", embedding=[0.0, 1.0] + [0.0]*(EMBED_DIM-2))

        results = top5_related([1.0] + [0.0]*(EMBED_DIM-1))

        self.assertEqual(results, ["q1", "q3", "q2"])
