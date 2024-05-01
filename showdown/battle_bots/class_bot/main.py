from data.team_datasets import TeamDatasets
from showdown.battle import Battle

import logging
from copy import deepcopy
logger = logging.getLogger(__name__)

from data.team_datasets import TeamDatasets
from showdown.battle import Battle
from ..helpers import format_decision
from showdown.engine.objects import StateMutator
from showdown.engine.select_best_move import get_payoff_matrix
from showdown.engine.select_best_move import pick_safest


class BattleBot(Battle):
    def __init__(self, *args, **kwargs):
        super(BattleBot, self).__init__(*args, **kwargs)

    def during_team_preview(self):
        opponent_pkmn_names = [p.name for p in self.opponent.reserve]
        TeamDatasets.set_pokemon_sets(opponent_pkmn_names)

        exact_team = TeamDatasets.get_exact_team(opponent_pkmn_names)
        if exact_team is not None:
            logger.info("Found an exact team")
            for pkmn, pkmn_info in exact_team.items():
                for pkmn_obj in self.opponent.reserve:
                    if pkmn_obj.name == pkmn:
                        split_info = pkmn_info.split("|")
                        pkmn_obj.ability = split_info[1]
                        pkmn_obj.item = split_info[2]
                        pkmn_obj.set_spread(
                            split_info[3],
                            split_info[4]
                        )
                        for m in split_info[5:]:
                            pkmn_obj.add_move(m)

    def find_best_move(self):
        # I will use alpha-beta pruning minimax search to determine the best move
        
        #initialize the battle
        battles = self.prepare_battles(join_moves_together=True)
        
        #find the best move
        def find_move_locally(passed_battles):
            # create a dict to store the scores
            all_scores = dict()
            search_depth = 3
            # get the battle object and get the current state of the game
            b = passed_battles[0]
            state = b.create_state()
            mutator = StateMutator(state)
            # get the options for the player and oppoenent in current state
            user_available_plays, opponent_available_plays = b.get_all_options()
            
            #iterate through the options
            num_user_plays = len(user_available_plays)
            num_opp_plays = len(opponent_available_plays)
            num_play_combinations = num_opp_plays * num_user_plays
            # check if there are enough possible states to search
            if num_play_combinations < 20 and num_user_plays > 1 and num_opp_plays > 1:
                search_depth += 1
            all_scores = get_payoff_matrix(mutator, user_available_plays, opponent_available_plays, depth = search_depth, prune=True)
            # get safest option from the engine
            decision, payoff = pick_safest(all_scores, remove_guaranteed=True)
            choice = decision[0]
            return choice
        
        # get the move
        decided_move = find_move_locally(battles)  
        
        #return the move
        return format_decision(self, decided_move)

