from django.test import TestCase
from django.contrib.auth.models import User
from secretsanta.models import Game, Player, Assignment, DependentProxy
from secretsanta.services.draw import draw_names, assign_proxies, DrawError

class ProxyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.game = Game.objects.create(owner=self.user, name='Test Game')
        
    def test_proxy_assignment(self):
        # P1 (Dep), P2, P3, P4
        p1 = Player.objects.create(game=self.game, name='P1', email='p1@example.com', is_dependent=True)
        p2 = Player.objects.create(game=self.game, name='P2', email='p2@example.com')
        p3 = Player.objects.create(game=self.game, name='P3', email='p3@example.com')
        p4 = Player.objects.create(game=self.game, name='P4', email='p4@example.com')
        
        draw_names(self.game)
        assign_proxies(self.game)
        
        proxy_assign = DependentProxy.objects.get(game=self.game, dependent=p1)
        
        # Proxy should not be P1
        self.assertNotEqual(proxy_assign.proxy, p1)
        
        # Proxy should not be the receiver of P1
        assignment = Assignment.objects.get(game=self.game, giver=p1)
        self.assertNotEqual(proxy_assign.proxy, assignment.receiver)

    def test_multiple_dependents_balanced(self):
        # Create many players to test balance
        players = []
        for i in range(10):
            is_dep = i < 4 # 4 dependents
            p = Player.objects.create(game=self.game, name=f'P{i}', email=f'p{i}@example.com', is_dependent=is_dep)
            players.append(p)
            
        draw_names(self.game)
        assign_proxies(self.game)
        
        proxies = DependentProxy.objects.filter(game=self.game)
        self.assertEqual(proxies.count(), 4)
        
        # Check that proxies are distributed
        proxy_counts = {}
        for p in proxies:
            pid = p.proxy.id
            proxy_counts[pid] = proxy_counts.get(pid, 0) + 1
            
        # Ideally max count should be low (e.g. 1 or 2)
        max_load = max(proxy_counts.values())
        self.assertLessEqual(max_load, 2) # With 10 players and 4 dependents, should be easy to have load 1
