import random
from secretsanta.models import Assignment, DependentProxy, ForbiddenPair

class DrawError(Exception):
    pass

def draw_names(game):
    """
    Performs the Secret Santa draw for a given game.
    Uses a backtracking algorithm to find a valid permutation.
    """
    players = list(game.players.all())
    if len(players) < 3:
        raise DrawError("Minimum 3 players required.")

    # Fetch forbidden pairs
    forbidden_pairs = set()
    for fp in game.forbidden_pairs.all():
        forbidden_pairs.add((fp.giver_id, fp.receiver_id))
        # Si es recíproca, también agregar la dirección inversa
        if fp.is_reciprocal:
            forbidden_pairs.add((fp.receiver_id, fp.giver_id))

    # We need to find a permutation where:
    # 1. giver != receiver
    # 2. (giver, receiver) not in forbidden_pairs
    # 3. Ideally, avoid cycles of length 2 if possible (optional, but good for fun), 
    #    but strict requirement is just validity.
    #    Let's stick to strict validity first.

    givers = players[:]
    receivers = players[:]
    
    # Shuffle receivers to ensure randomness
    random.shuffle(receivers)

    assignment_map = {} # giver_id -> receiver_id

    def backtrack(index):
        if index == len(givers):
            return True

        giver = givers[index]
        
        for i in range(index, len(receivers)):
            # Swap current receiver candidate to position 'index'
            receivers[index], receivers[i] = receivers[i], receivers[index]
            
            receiver = receivers[index]
            
            # Check constraints
            if giver.id == receiver.id:
                # Cannot give to self
                pass
            elif (giver.id, receiver.id) in forbidden_pairs:
                # Forbidden pair
                pass
            else:
                # Valid so far, recurse
                if backtrack(index + 1):
                    assignment_map[giver.id] = receiver.id
                    return True
            
            # Backtrack: swap back
            receivers[index], receivers[i] = receivers[i], receivers[index]
            
        return False

    if not backtrack(0):
        raise DrawError("No valid assignment found. Try removing some restrictions.")

    # Save assignments
    # Clear old assignments first (though logic should handle this before calling)
    Assignment.objects.filter(game=game).delete()
    
    new_assignments = []
    player_map = {p.id: p for p in players}
    
    for giver_id, receiver_id in assignment_map.items():
        new_assignments.append(
            Assignment(
                game=game,
                giver=player_map[giver_id],
                receiver=player_map[receiver_id]
            )
        )
    
    Assignment.objects.bulk_create(new_assignments)
    
    return True

def assign_proxies(game):
    """
    Assigns proxies for dependent players.
    """
    dependents = list(game.players.filter(is_dependent=True))
    if not dependents:
        return

    # Clear old proxies
    DependentProxy.objects.filter(game=game).delete()

    # Get all potential proxies (non-dependents could be proxies, but dependents can also be proxies? 
    # Requirement: "proxy -> otro jugador del mismo juego". 
    # Usually a proxy is a responsible adult. Let's assume anyone can be a proxy unless specified otherwise.
    # But wait, "El dependiente no puede regalar a su proxy." -> This is a constraint on the draw, or on the proxy selection?
    # "El dependiente no puede regalar a su proxy" implies we need to check the assignment.
    
    # Let's fetch assignments to check constraints
    assignments = {a.giver_id: a.receiver_id for a in game.assignments.all()}
    
    all_players = list(game.players.all())
    potential_proxies = all_players[:] # Copy
    
    # Constraint: Proxy must be distinct from dependent.
    # Constraint: Proxy cannot be the receiver of the dependent. 
    # (Dependent gives to X, so Proxy cannot be X).
    
    # We need to distribute proxies effectively.
    # If there are multiple dependents, we want to balance the load on proxies.
    
    proxy_counts = {p.id: 0 for p in all_players}
    
    new_proxies = []
    
    # Shuffle dependents to avoid bias
    random.shuffle(dependents)
    
    for dep in dependents:
        # Filter valid candidates
        candidates = []
        for p in all_players:
            # 1. Proxy != Dependent
            if p.id == dep.id:
                continue
            
            # 2. Proxy != Dependent's Receiver
            # Who is dependent giving to?
            dep_receiver_id = assignments.get(dep.id)
            if p.id == dep_receiver_id:
                continue
                
            candidates.append(p)
        
        if not candidates:
            raise DrawError(f"Could not find a valid proxy for {dep.name}")
        
        # Select candidate with minimum current proxy load
        # Sort by load, then random
        random.shuffle(candidates)
        candidates.sort(key=lambda p: proxy_counts[p.id])
        
        chosen_proxy = candidates[0]
        proxy_counts[chosen_proxy.id] += 1
        
        new_proxies.append(
            DependentProxy(
                game=game,
                dependent=dep,
                proxy=chosen_proxy
            )
        )
        
    DependentProxy.objects.bulk_create(new_proxies)
