from pydantic import BaseModel, Field
from typing import Literal

GenehmigungLiteral = Literal["Ja", "Nein", "Manuelle Prüfung"]

class DecisionOut(BaseModel):
    Genehmigung: GenehmigungLiteral
    Genehmigungsbetrag: float = Field(0.0, ge=0.0)
    Empfehlung: str = ""

    # Minimaler Guard: Wenn Ja, dann Betrag > 0 (rudimentär)
    def model_post_init(self, __context):
        if self.Genehmigung == "Ja" and self.Genehmigungsbetrag <= 0:
            # Für Machbarkeit lieber hart auf Manuelle Prüfung zurück
            self.Genehmigung = "Manuelle Prüfung"
            self.Genehmigungsbetrag = 0.0
            if not self.Empfehlung:
                self.Empfehlung = "Genehmigung=Ja erfordert positiven Genehmigungsbetrag."
        if self.Genehmigung != "Ja":
            self.Genehmigungsbetrag = 0.0
