# 📋 CHARTE ÉTHIQUE & RGPD
## Plateforme Prédictive CEVA Logistics

**Date:** Mars 2025 | **Auteur:** Dorian

---

## 🔐 CONFORMITÉ RGPD

### Anonymisation
✅ Références clients masquées (Customer_Reference)
✅ Aucun nom, email, téléphone
✅ Shipment_ID anonymisés

### Usage données
✅ Strictement académique (Master AI/Data PM)
✅ Pas de commercialisation
✅ Suppression post-soutenance

### Sécurité
✅ Stockage local sécurisé
✅ Pas de partage cloud public
✅ Accès restreint (étudiant + tuteurs)

---

## ⚖️ BIAIS & ÉQUITÉ

### Biais identifiés
⚠️ **Carrier bias:** Certains carriers surreprésentés (DHL 14%)
⚠️ **Geographic bias:** Routes EU dominantes vs pays tiers (6%)
⚠️ **Temporal bias:** 2 ans données (pas décennies)

### Mesures atténuation
✅ Validation croisée temporelle (pas aléatoire)
✅ Métriques équité par sous-groupe (BU, routes, carriers)
✅ Transparence limitations dans mémoire

---

## 🎯 ÉTHIQUE PRÉDICTIONS

### Principes
1. **Transparence:** Modèles explicables (SHAP, feature importance)
2. **Non-discrimination:** Pas de bias contre carriers/pays
3. **Usage responsable:** Alertes, pas décisions automatiques
4. **Contrôle humain:** Dispatchers décident, ML suggère
5. **Amélioration continue:** Monitoring biais, retraining

### Usages interdits
❌ Pénaliser carriers sans investigation
❌ Refuser shipments basé uniquement sur prédictions
❌ Discriminer pays/régions

---

## 📊 QUALITÉ & LIMITATIONS

### Transparence données
- 32k lignes AIR (ROAD/SEA exclus)
- 25 mois (pas représentatif long terme)
- Données partiellement synthétisées (confidentialité)

### Limitations modèles
- Pas de variables externes (météo, grèves)
- Pas de données coûts réels (estimés)
- Performances non garanties hors période

---

**Validation:** Document à joindre en annexe mémoire
