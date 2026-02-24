# Comprehensive dermatology labels based on EU prevalence and referral guidelines
# Rationale:
# 1. Malignant/Pre-malignant: Detecting high-mortality (Melanoma) and high-prevalence (BCC/SCC) cancers is the priority.
# 2. Inflammatory: Eczema, Psoriasis, and Acne are the most common burdens on quality of life in EU.
# 3. Infectious: Fungal and viral infections are frequent reasons for primary care visits.
# 4. Benign: Essential for differential diagnosis to reduce unnecessary anxiety or referrals.

MEDSIGLIP_DERMATOLOGY_LABELS = {
    # Malignant & Pre-malignant
    "Melanoma": "malignant melanoma, asymmetric pigmented lesion with irregular borders and color variegation",
    "Basal Cell Carcinoma": "basal cell carcinoma, pearly translucent papule with arborizing telangiectasia",
    "Squamous Cell Carcinoma": "squamous cell carcinoma, indurated hyperkeratotic erythematous nodule or ulcerated plaque",
    "Actinic Keratosis": "actinic keratosis, rough scaly erythematous macule on sun-damaged skin",
    "Bowen's Disease": "Bowen's disease, well-demarcated erythematous scaly plaque",
    "Dysplastic Nevus": "dysplastic nevus, atypical melanocytic lesion with irregular borders and variable pigmentation",
    
    # Benign Tumors (Differential Diagnosis)
    "Melanocytic Nevus": "benign melanocytic nevus, well-circumscribed symmetrical pigmented macule",
    "Seborrheic Keratosis": "seborrheic keratosis, sharply demarcated verrucous plaque with stuck-on appearance",
    "Dermatofibroma": "dermatofibroma, firm hyperpigmented dermal nodule with positive dimple sign",
    "Haemangioma": "hemangioma, benign vascular anomaly, bright red or violaceous nodule",
    "Epidermoid Cyst": "epidermoid cyst, subcutaneous skin-colored nodule with central punctum",
    
    # Inflammatory Conditions
    "Psoriasis": "psoriasis vulgaris, well-demarcated erythematous plaques with thick silvery-white scale",
    "Atopic Dermatitis": "atopic dermatitis, pruritic erythematous scaling patches with lichenification",
    "Acne Vulgaris": "acne vulgaris, inflammatory eruption with comedones, papules, and pustules",
    "Rosacea": "rosacea, facial erythema and telangiectasia with inflammatory papules",
    "Urticaria": "urticaria, transient circumscribed erythematous and edematous wheals",
    "Lichen Planus": "lichen planus, pruritic purple polygonal planar papules with Wickham striae",
    "Hidradenitis Suppurativa": "hidradenitis suppurativa, painful deep-seated inflammatory nodules and abscesses",
    
    # Infectious
    "Fungal Infection": "tinea fungal infection, an annular, scaling, erythematous patch with raised borders and central clearing",
    "Herpes Zoster": "herpes zoster, a unilateral, dermatomal eruption of grouped, painful vesicles on an erythematous base",
    "Impetigo": "impetigo, superficial bacterial infection with erosions and classic honey-colored crusting",
    "Warts": "verruca vulgaris, a viral infection presenting as a hyperkeratotic, exophytic papule",
    "Molluscum Contagiosum": "molluscum contagiosum, presenting as firm, dome-shaped, umbilicated, pearly papules",
    
    # Pigmentary & Hair
    "Vitiligo": "vitiligo, depigmented white macules and patches devoid of melanocytes",
    "Alopecia Areata": "alopecia areata, localized patches of non-scarring hair loss on the scalp or body",
    "Melasma": "melasma, symmetric, hyperpigmented brown macules primarily on sun-exposed facial areas",

    # Miscellaneous 
    "Insect Bites": "arthropod bite reaction, intensely pruritic, erythematous papules with a central punctum",
    "Folliculitis": "folliculitis, inflammation of hair follicles with multiple erythematous papules and pustules",
    "Drug Rash": "morbilliform drug eruption, a generalized, symmetric, maculopapular erythematous exanthem",
    
    # Baseline
    "Normal Skin": "normal, healthy skin with intact epidermis, uniform texture, and no visible lesions"
}
#Inflammatory vs. Neoplastic Differentiation: The model can effectively distinguish 
# between inflammatory skin conditions and neoplastic (cancerous) 
## Used for triage analysis
MEDSIGLIP_DERMATOLOGY_FIRST_CLASSES = {
    # 1. Inflammatory 
    "Inflammatory skin disease": "showing inflammatory lesion, or a rash or redness, or scaling",
    # 2. Neoplastic 
    #"Neoplastic skin tumor": "neoplastic skin tumor or suspect growth or abnormal mole",
    "Melanoma": MEDSIGLIP_DERMATOLOGY_LABELS["Melanoma"],
    # 3. Zero-Shot Baseline
    "Healthly skin": "melanocytic naevus, pigmented naevus"
}

CANCEROUS_TUMOR_CLASSES = {
    "Melanoma", 
    "Basal Cell Carcinoma",
    "Squamous Cell Carcinoma",
    "Bowen's Disease"
}

BENIGN_TUMOR_CLASSES = {
    "Melanocytic Nevus",
    "Seborrheic Keratosis",
    "Dermatofibroma",
    "Haemangioma",
    "Epidermoid Cyst"
}

# Narrow set of labels focusing on MedSigLIP's highest performance tiers
MEDSIGLIP_DERMATOLOGY_NARROW_LABELS = {
    # 1. High-Precision Vascular & Pigmented Lesions
    "Melanoma": MEDSIGLIP_DERMATOLOGY_LABELS["Melanoma"],
    "Basal Cell Carcinoma": MEDSIGLIP_DERMATOLOGY_LABELS["Basal Cell Carcinoma"],
    "Melanocytic Nevus": MEDSIGLIP_DERMATOLOGY_LABELS["Melanocytic Nevus"],
    "Seborrheic Keratosis": MEDSIGLIP_DERMATOLOGY_LABELS["Seborrheic Keratosis"],
    
    # 2. Texture-Heavy Inflammatory Conditions
    "Psoriasis": MEDSIGLIP_DERMATOLOGY_LABELS["Psoriasis"],
    "Atopic Dermatitis": MEDSIGLIP_DERMATOLOGY_LABELS["Atopic Dermatitis"],
    "Acne Vulgaris": MEDSIGLIP_DERMATOLOGY_LABELS["Acne Vulgaris"],
    "Rosacea": MEDSIGLIP_DERMATOLOGY_LABELS["Rosacea"],
    
    # 3. Morphologically Distinct Infections
    "Herpes Zoster": MEDSIGLIP_DERMATOLOGY_LABELS["Herpes Zoster"],
    "Warts": MEDSIGLIP_DERMATOLOGY_LABELS["Warts"],
    "Molluscum Contagiosum": MEDSIGLIP_DERMATOLOGY_LABELS["Molluscum Contagiosum"],
    
    # 4. Zero-Shot Baseline
    "Normal Skin": MEDSIGLIP_DERMATOLOGY_LABELS["Normal Skin"]
}


