# coding: utf-8

class MaterialGroup:
    PLASTIC = "plastic"
    METAL = "metal"
    GLASS = "glass"
    PAPER = "paper"
    COMPOSITE = "composite"
    E_WASTE = "e_waste"
    TEXTILE = "textile"
    OTHER = "other"

ECO_COEFFICIENTS = {
    "metal_iron": {
        "name": "Железо / Чермет (FE 40)",
        "group": MaterialGroup.METAL,
        "coefficient": 1.5,
        "unit": "kg"
    },
    "metal_aluminum": {
        "name": "Алюминий / Алюминиевые банки (ALU 41)",
        "group": MaterialGroup.METAL,
        "coefficient": 4.0,
        "unit": "kg"
    },
    "metal_other": {
        "name": "Прочий металл (Крепления, пластины, покрыватель)",
        "group": MaterialGroup.METAL,
        "coefficient": 2.0,
        "unit": "kg"
    },
    "glass_container": {
        "name": "Стекло тарное (70-74 GL)",
        "group": MaterialGroup.GLASS,
        "coefficient": 1.0,
        "unit": "kg"
    },
    "plastic_pet_bottle": {
        "name": "ПЭТ-бутылка (1 PET/PETE) - с крышкой",
        "group": MaterialGroup.PLASTIC,
        "coefficient": 3.5,
        "unit": "kg",
        "note": "Если сдана с крышкой, +0.5 бонуса (учтено в коэф.)"
    },
    "plastic_hdpe_canister": {
        "name": "Канистры / Флаконы HDPE (2 PE-HD)",
        "group": MaterialGroup.PLASTIC,
        "coefficient": 3.0,
        "unit": "kg"
    },
    "plastic_ldpe_bag": {
        "name": "Пакеты / Пленка LDPE (4 PE-LD, ПВД)",
        "group": MaterialGroup.PLASTIC,
        "coefficient": 4.5,
        "unit": "kg"
    },
    "plastic_pp_bag": {
        "name": "Мешки полипропиленовые (5 PP)",
        "group": MaterialGroup.PLASTIC,
        "coefficient": 3.0,
        "unit": "kg"
    },
    "small_plastic_cap": {
        "name": "Крышки пластиковые (кепки)",
        "group": MaterialGroup.PLASTIC,
        "coefficient": 8.0,
        "unit": "kg"
    },
    "plastic_cards": {
        "name": "Пластиковые карты / Дисконтные карты",
        "group": MaterialGroup.PLASTIC,
        "coefficient": 12.0,
        "unit": "kg",
        "note": "Учитывать как 5 грамм за штуку"
    },
    "plastic_legacy_toys": {
        "name": "Игрушки пластиковые (LEGO, конструкторы СССР)",
        "group": MaterialGroup.PLASTIC,
        "coefficient": 6.0,
        "unit": "kg"
    },
    "composite_tetrapak": {
        "name": "Тетра-Пак / Пюр-Пак (C/PAP 84, PAP 21-22)",
        "group": MaterialGroup.COMPOSITE,
        "coefficient": 7.0,
        "unit": "kg",
        "note": "Сложный многокомпонентный материал"
    },
    "cd_dvd": {
        "name": "CD / DVD диски (без коробки)",
        "group": MaterialGroup.COMPOSITE,
        "coefficient": 15.0,
        "unit": "kg",
        "note": "Поликарбонат с напылением. Очень высокая ценность сдачи"
    },
    "textile": {
        "name": "Текстиль (одежда, ветошь на переработку)",
        "group": MaterialGroup.TEXTILE,
        "coefficient": 2.5,
        "unit": "kg"
    },
    "books": {
        "name": "Книги (макулатура высокого качества)",
        "group": MaterialGroup.PAPER,
        "coefficient": 1.8,
        "unit": "kg"
    },
    "silicone": {
        "name": "Силиконовые формы / Покрытия",
        "group": MaterialGroup.OTHER,
        "coefficient": 9.0,
        "unit": "kg",
        "note": "Редко перерабатывается, высокий бонус за ответственный подход"
    }
}