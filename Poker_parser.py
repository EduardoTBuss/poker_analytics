import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PokerParser:
    
    POSITION_NAMES = ['SB', 'BB', 'UTG', 'MP', 'CO', 'BTN']
    
    def __init__(self):
        self.hands = []
        self.errors = []
    
    def parse_directory(self, base_path: str) -> None:
        
        base_path = Path(base_path)
        
        session_dirs = sorted(
            [d for d in base_path.iterdir() if d.is_dir()],
            key=lambda x: (int(re.sub(r'\D', '', x.name)), x.name)
        )
        
        total_files = sum(len(list(d.glob("*.phh"))) for d in session_dirs)
        logger.info(f"Encontradas {len(session_dirs)} sessões, {total_files} arquivos")
        
        with tqdm(total=total_files, desc="Processando") as pbar:
            for session_dir in session_dirs:
                self._parse_session(session_dir, pbar)
        
        logger.info(f"{len(self.hands)} mãos processadas")
        if self.errors:
            logger.warning(f"{len(self.errors)} erros encontrados")
    
    def _parse_session(self, session_dir: Path, pbar: tqdm) -> None:
        session_id = session_dir.name
        phh_files = sorted(session_dir.glob("*.phh"), key=lambda x: int(x.stem))
        
        for phh_file in phh_files:
            try:
                self._parse_file(phh_file, session_id)
            except Exception as e:
                self.errors.append(f"{session_id}/{phh_file.name}: {str(e)}")
            pbar.update(1)
    
    def _parse_file(self, filepath: Path, session_id: str) -> None:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        hand_texts = [h for h in re.split(r'(?=variant\s*=)', content) if h.strip()]
        
        for hand_text in hand_texts:
            hand_data = self._parse_hand(hand_text, session_id, filepath.stem)
            if hand_data:
                self.hands.append(hand_data)
    
    def _parse_hand(self, text: str, session_id: str, file_id: str) -> Optional[Dict]:
        try:
            players = self._extract_list(r'players\s*=\s*\[(.*?)\]', text)
            starting_stacks = self._extract_list(
                r'starting_stacks\s*=\s*\[(.*?)\]', text, as_int=True
            )
            finishing_stacks = self._extract_list(
                r'finishing_stacks\s*=\s*\[(.*?)\]', text, as_int=True
            )
            blinds = self._extract_list(
                r'blinds_or_straddles\s*=\s*\[(.*?)\]', text, as_int=True
            )
            actions_str = self._extract_list(
                r'actions\s*=\s*\[(.*?)\]', text, raw=True
            )
            hand_num = self._extract(r'hand\s*=\s*(\d+)', text)
            
            if not all([players, starting_stacks, finishing_stacks, actions_str]):
                return None
            
            hand_id = f"{session_id}_{file_id}_{hand_num or '0'}"
            
            hole_cards, actions_by_street, board = self._process_actions(
                actions_str, players
            )
            
            record = {
                'session': session_id,
                'hand_id': hand_id,
                'small_blind': blinds[0] if blinds else 0,
                'big_blind': blinds[1] if blinds and len(blinds) > 1 else 0,
                'num_players': len(players),
                'actions_preflop': actions_by_street.get('preflop', ''),
                'actions_flop': actions_by_street.get('flop', ''),
                'actions_turn': actions_by_street.get('turn', ''),
                'actions_river': actions_by_street.get('river', ''),
                'flop': board.get('flop'),
                'turn': board.get('turn'),
                'river': board.get('river'),
            }
            
            for i, player in enumerate(players):
                pos = self.POSITION_NAMES[i] if i < len(self.POSITION_NAMES) else f'P{i+1}'
                record[f'player_{i+1}'] = player
                record[f'position_{i+1}'] = pos
                record[f'hole_cards_{i+1}'] = hole_cards.get(i+1)
                record[f'starting_stack_{i+1}'] = starting_stacks[i]
                record[f'finishing_stack_{i+1}'] = finishing_stacks[i]
                record[f'profit_{i+1}'] = finishing_stacks[i] - starting_stacks[i]
            
            return record
        
        except Exception as e:
            logger.debug(f"Erro ao processar mão: {e}")
            return None
    
    def _process_actions(
        self, actions: List[str], players: List[str]
    ) -> Tuple[Dict, Dict, Dict]:
        
        CARD_RE = re.compile(r'(?:10|[2-9TJQKA])[cdhs]', re.IGNORECASE)
        
        hole_cards = {}
        actions_by_street = {'preflop': [], 'flop': [], 'turn': [], 'river': []}
        board_cards_list = []
        current_street = 'preflop'
        
        for action in actions:
            action = action.strip()
            cards = CARD_RE.findall(action)
            
            if action.startswith('d dh'):
                m = re.search(r'p(\d+)', action)
                if m and len(cards) >= 2:
                    player_num = int(m.group(1))
                    hole_cards[player_num] = f"{cards[-2]} {cards[-1]}"
                continue
            
            if action.startswith('d') and not action.startswith('d dh'):
                if cards:
                    board_cards_list.extend(cards)
                    count = len(board_cards_list)
                    
                    if count == 3:
                        current_street = 'flop'
                    elif count == 4:
                        current_street = 'turn'
                    elif count >= 5:
                        current_street = 'river'
                continue
            
            if action.startswith('p'):
                parts = action.split()
                try:
                    p_match = re.search(r'p(\d+)', parts[0])
                    if not p_match:
                        continue
                    player_num = int(p_match.group(1))
                except:
                    continue
                
                action_code = parts[1] if len(parts) > 1 else ''
                
                action_map = {
                    'f': 'fold',
                    'cc': 'call',
                    'cbr': 'bet_raise',
                    'c': 'check',
                    'b': 'bet',
                    'r': 'raise',
                    'k': 'check'
                }
                
                action_name = action_map.get(action_code, action_code)
                
                amount = ""
                if len(parts) > 2 and parts[2].replace('.', '', 1).isdigit():
                    amount = f" {parts[2]}"
                    if action_name == 'bet_raise':
                        action_name = 'raise'
                
                actions_by_street[current_street].append(
                    f"P{player_num}:{action_name}{amount}"
                )
        
        board = {}
        if len(board_cards_list) >= 3:
            board['flop'] = " ".join(board_cards_list[:3])
        if len(board_cards_list) >= 4:
            board['turn'] = board_cards_list[3]
        if len(board_cards_list) >= 5:
            board['river'] = board_cards_list[4]
        
        for street in actions_by_street:
            actions_by_street[street] = ', '.join(actions_by_street[street])
        
        return hole_cards, actions_by_street, board
    
    def _extract(self, pattern: str, text: str) -> Optional[str]:
        match = re.search(pattern, text)
        return match.group(1) if match else None
    
    def _extract_list(
        self, pattern: str, text: str, as_int: bool = False, raw: bool = False
    ) -> Optional[List]:
        match = re.search(pattern, text, re.DOTALL if raw else 0)
        if not match:
            return None
        
        if raw:
            try:
                return eval(f'[{match.group(1)}]')
            except Exception:
                return []
        
        content = match.group(1)
        if as_int:
            return [int(x) for x in re.findall(r'\d+', content)]
        return [s.strip().strip("'\"") for s in content.split(',') if s.strip()]
    
    def to_hands_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame(self.hands)
        cols = [
            'session', 'hand_id', 'small_blind', 'big_blind', 'num_players',
            'actions_preflop', 'actions_flop', 'actions_turn', 'actions_river',
            'flop', 'turn', 'river'
        ]
        return df[[c for c in cols if c in df.columns]]
    
    def to_players_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame(self.hands)
        rows = []
        
        for _, r in df.iterrows():
            for i in range(1, 7):
                player = r.get(f'player_{i}')
                if pd.isna(player):
                    continue
                rows.append({
                    'session': r['session'],
                    'hand_id': r['hand_id'],
                    'player': player,
                    'position': r.get(f'position_{i}'),
                    'hole_cards': r.get(f'hole_cards_{i}'),
                    'starting_stack': r.get(f'starting_stack_{i}'),
                    'finishing_stack': r.get(f'finishing_stack_{i}'),
                    'profit': r.get(f'profit_{i}')
                })
        
        return pd.DataFrame(rows)
    
    def save(self, output_dir: str = 'data') -> None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        hands_df = self.to_hands_dataframe()
        players_df = self.to_players_dataframe()
        
        hands_df.to_csv(output_dir / 'hands.csv', index=False)
        hands_df.to_parquet(output_dir / 'hands.parquet', index=False)
        
        players_df.to_csv(output_dir / 'players_in_hand.csv', index=False)
        players_df.to_parquet(output_dir / 'players_in_hand.parquet', index=False)
        
        logger.info(f"Hands: {len(hands_df)} mãos salvas")
        logger.info(f"Players: {len(players_df)} registros de jogadores salvos")
        logger.info(f"Arquivos salvos em: {output_dir}")

        if self.errors:
            error_file = output_dir / 'parse_errors.log'
            with open(error_file, 'w') as f:
                f.write('\n'.join(self.errors))
            logger.info(f"Log de erros: {error_file}")


def create_dataset(
    pluribus_path: str = 'pluribus',
    output_dir: str = 'data',
    return_dataframes: bool = False
) -> Optional[Tuple[pd.DataFrame, pd.DataFrame]]:
    
    print("="*80)
    print(" "*25 + "POKER DATASET BUILDER")
    print("="*80)
    print()
    
    if not Path(pluribus_path).exists():
        logger.error(f"Caminho não encontrado: {pluribus_path}")
        return None
    
    parser = PokerParser()
    parser.parse_directory(pluribus_path)
    
    parser.save(output_dir)
   
    print(f"Arquivos gerados em: {output_dir}/")
    print("hands.csv")
    print("hands.parquet")
    print("players_in_hand.csv")
    print("players_in_hand.parquet")
    print()

    if return_dataframes:
        return parser.to_hands_dataframe(), parser.to_players_dataframe()
    
    return None