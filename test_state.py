from src.core.state import FixtureState

try:
    f = FixtureState()
    print(f"Test de création de FixtureState...")
    print(f"pos_x existe ? : {hasattr(f, 'pos_x')}")
    print(f"Valeur de pos_x : {f.pos_x}")
    print("TOUT EST OK !" if hasattr(f, 'pos_x') else "ERREUR : pos_x manque !")
except Exception as e:
    print(f"CRASH : {e}")