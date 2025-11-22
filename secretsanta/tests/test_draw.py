from django.test import TestCase
from django.contrib.auth.models import User
from secretsanta.models import Game, Player, ForbiddenPair, Assignment
from secretsanta.services.draw import draw_names, DrawError

class DrawTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.game = Game.objects.create(owner=self.user, name='Test Game')
        
    def test_draw_simple(self):
        # Create 3 players
        p1 = Player.objects.create(game=self.game, name='P1', email='p1@example.com')
        p2 = Player.objects.create(game=self.game, name='P2', email='p2@example.com')
        p3 = Player.objects.create(game=self.game, name='P3', email='p3@example.com')
        
        success = draw_names(self.game)
        self.assertTrue(success)
        
        assignments = Assignment.objects.filter(game=self.game)
        self.assertEqual(assignments.count(), 3)
        
        # Verify no self-assignment
        for a in assignments:
            self.assertNotEqual(a.giver, a.receiver)
            
        # Verify uniqueness
        givers = set(a.giver for a in assignments)
        receivers = set(a.receiver for a in assignments)
        self.assertEqual(len(givers), 3)
        self.assertEqual(len(receivers), 3)

    def test_draw_forbidden(self):
        # P1, P2, P3
        p1 = Player.objects.create(game=self.game, name='P1', email='p1@example.com')
        p2 = Player.objects.create(game=self.game, name='P2', email='p2@example.com')
        p3 = Player.objects.create(game=self.game, name='P3', email='p3@example.com')
        
        # P1 cannot give to P2
        ForbiddenPair.objects.create(game=self.game, giver=p1, receiver=p2)
        
        # Run multiple times to ensure stability
        for _ in range(5):
            draw_names(self.game)
            a1 = Assignment.objects.get(game=self.game, giver=p1)
            self.assertNotEqual(a1.receiver, p2)

    def test_draw_impossible(self):
        # P1, P2, P3
        p1 = Player.objects.create(game=self.game, name='P1', email='p1@example.com')
        p2 = Player.objects.create(game=self.game, name='P2', email='p2@example.com')
        p3 = Player.objects.create(game=self.game, name='P3', email='p3@example.com')
        
        # Create a cycle of forbidden pairs that makes it impossible?
        # With 3 players:
        # P1 -> P2 forbidden
        # P1 -> P3 forbidden
        # P1 must give to someone!
        ForbiddenPair.objects.create(game=self.game, giver=p1, receiver=p2)
        ForbiddenPair.objects.create(game=self.game, giver=p1, receiver=p3)
        
        with self.assertRaises(DrawError):
            draw_names(self.game)
