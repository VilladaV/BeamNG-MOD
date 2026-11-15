import hashlib
import io
import json
import re
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from PIL import Image, ImageChops, ImageStat

MODS_ROOT = Path(r"C:\Users\johan\AppData\Local\BeamNG\BeamNG.drive\current\mods")
PROJECT_ROOT = Path(r"C:\Users\johan\orca\workspaces\GlobalBerrs\BeamNG")
OUT_JSON = PROJECT_ROOT / "src" / "data" / "modsCatalog.json"
MAPS_THUMB_DIR = PROJECT_ROOT / "public" / "thumbnails" / "maps"
CARS_THUMB_DIR = PROJECT_ROOT / "public" / "thumbnails" / "cars"
CACHE_DIR = Path(r"C:\Users\johan\.gemini\antigravity-cli\brain\6e4d0edc-c889-4359-a7f7-1a68e2c77300\scratch")
CACHE_FILE = CACHE_DIR / "wiki_image_v2_cache.json"
COMMONS_CACHE_FILE = CACHE_DIR / "commons_gallery_cache.json"

USER_AGENT = "BeamNGModsGalleryBot/1.0 (https://github.com/VilladaV/BeamNG-MOD)"

VANILLA_VEHICLES = {
    "autobello", "barstow", "bastion", "bluebuck", "bolide", "burnside", "bx",
    "citybus", "covet", "dunekicker", "etk800", "etkc", "etki", "fullsize",
    "grandmarshal", "hopper", "lansdale", "legran", "md_series", "midsize",
    "miramar", "moonhawk", "nine", "pessima", "pigeon", "pickup", "racetruck",
    "roamer", "rockbouncer", "sbr", "scintilla", "semi", "sp_dunekicker",
    "sp_rockbouncer", "stambecco", "sunburst", "sunburst2", "us_semi", "utv", "van",
    "vivace", "wendover", "wigeon", "common", "200bx", "coupe", "hatch", "super",
    "midtruck", "atv", "dumptruck", "segra", "percheron", "simple_traffic",
    "dryvan", "flatbed", "tanker", "boxutility", "boxutility_large", "dolly",
    "caravan", "cargotrailer", "containertrailer", "dollies", "frameless_dump",
    "log_trailer", "lowboy", "tiltdeck", "tsfb", "tub_trailer",
}

SKIP_CAR_ZIPS = {
    # Non-cars: trailers, motorcycles, bicycles, tanks, boats, buses, motorhomes
    "1790629280392-detachable-gooseneck-lowboy-trailer-1-0.zip",
    "hh_110t_steerable_test1_modland.zip",
    "maz8114pricepver1.0.zip",
    "tanker_pickup_sandwichesandmilk.zip",
    "bicycle_12_tuning_patch_v27_2025_by_elitegarage_modland.zip",
    "yamaha_yzf-r15_advanced_version_v34_2023_by_speedline_modland.zip",
    "aerox mutapalli addons.zip",
    "iran__honda_cb_1000_modland.zip",
    "mankifix_mutapalli.zip",  # Honda Monkey minibike
    "vt-4_tank_v3.0.zip",
    "irp.zip",  # Sea-Geon boat
    "3axlecitybus.zip",
    "g81800dd.zip",
    "ikarus_55_lux_modland.zip",
    "jaero_bus_modland.zip",
    "kavz685final_modland.zip",
    "lionscoachbeta.zip",
    "maz103.103restpublicver1.0.zip",
    "maz206.226remasterver1.0.zip",
    "neoplan_modland.zip",
    "scania omnilink ii.zip",
    "urb_daewon_coachframe.zip",
    "urbinoiv_fixed.zip",
    "xl45_motorhome_v1.2_by_grade8.zip",
    # Pure patches / addons / engine packs / config packs
    "lot72d_patch.zip",
    "renaultloganmk1_addon_hotfix.zip",
    "bugexpansion.zip",
    "megapak_ssrg.zip",
    "procyon_apex_performance.zip",
    "satsuma210_rotary_detuned.zip",
    "scout_addons.zip",
    "shimaparts_s1a.zip",
    "tango_twingo_engines.zip",
    "touringhugepackv2.zip",
    "wbimp_bg1234.zip",
    "iretr0x_dfa.zip",
    "picnic_awd_miata_lover.zip",
    "mistral_awd.zip",
    "talent_export_models.zip",
    # Duplicate zip copies
    "lamborghiniaventador_modland.zip",
    "m6f13.zip",
}

SKIP_MAP_ZIPS = {
    "gt4_george_v_paris_v1_modland (1).zip",
    "three_passes_v0.9.0_modland.zip",
    "huge_desert_ver5.zip",
}

# Exact Wikipedia article titles for BeamNG Lore / obscure car mods -> real-world car counterpart
LORE_AND_EXACT_CAR_MAP = {
    "05 mustang gt.zip": ("Ford Mustang (fifth generation)", "2005 Ford Mustang GT"),
    "1967 mercedes-benz 280sl.zip": ("Mercedes-Benz SL-Class (W113)", "1967 Mercedes-Benz 280SL"),
    "1995subub.zip": ("Chevrolet Suburban (eighth generation)", "1995 Chevrolet Suburban GMT400"),
    "1volga_21_dynamic_release_v16_2025_by_beamfixer_modland.zip": ("GAZ-21", "GAZ-21 Volga"),
    "2006-2014_smart_fortwo_451_035fixmb_dynamic_edition_v1.1_2025_by_georgi.zip": ("Smart Fortwo", "Smart Fortwo (451)"),
    "2020_audi_rs5_b9_modland.zip": ("Audi RS5 B9", "Audi RS 5 (B9)"),
    "2022-hyundai-casper-v3-05-0-37-x_1760375345_563321_dynamic_patch_v15_2024_by_autobeam_modland.zip": ("Hyundai Casper", "Hyundai Casper"),
    "3series_f30.zip": ("BMW 3 Series (F30)", "BMW 3 Series (F30)"),
    "90094-daewoo-nexia-sedan-2000-v20.zip": ("Daewoo Nexia", "Daewoo Nexia"),
    "911_996.zip": ("Porsche 911 (996)", "Porsche 911 (996)"),
    "acm_haval_f7_gr_22_07_2025_final.zip": ("Haval F7", "Haval F7"),
    "ananda_andika_suzuki_carry.zip": ("Suzuki Carry", "Suzuki Carry"),
    "audi q7 v1.2 & tg_m0dsbeamng.zip": ("Audi Q7", "Audi Q7"),
    "audi rs3 fix 0.29.zip": ("Audi RS 3", "Audi RS 3 (8Y)"),
    "audi-rs-e-tron-gt-2021_modland.zip": ("Audi e-tron GT", "Audi RS e-tron GT"),
    "audi_a4_modland.zip": ("Audi A4", "Audi A4 (B9)"),
    "audi_a8_modland.zip": ("Audi A8", "Audi A8L"),
    "audi_rs6_c7_modland.zip": ("Audi RS 6", "Audi RS 6 Avant (C7)"),
    "audi_tt_mk3.zip": ("Audi TT", "Audi TT (8S Mk3)"),
    "autobello aria.zip": ("Fiat 126", "Autobello Aria (Fiat 126)"),
    "avantime_v5_hotfix1.zip": ("Renault Avantime", "Renault Avantime"),
    "aveot300_modland.zip": ("Chevrolet Aveo", "Chevrolet Aveo (T300)"),
    "aw-ford ranger-20230902t141904z-001_modland.zip": ("Ford Ranger (T6)", "Ford Ranger"),
    "bailey_5th_gen_camaro.zip": ("Chevrolet Camaro (fifth generation)", "Chevrolet Camaro (5th Gen)"),
    "beachbuggy.zip": ("Meyers Manx", "Autobello Beach Buggy (Meyers Manx)"),
    "beetle_1.1_modland.zip": ("Volkswagen New Beetle", "Volkswagen New Beetle"),
    "bmw m3 e90.zip": ("BMW 3 Series (E90)", "BMW M3 (E90)"),
    "bmw m5 g90.zip": ("BMW M5", "BMW M5 (G90)"),
    "bmw m8 f92 revamped.zip": ("BMW 8 Series (G15)", "BMW M8 (F92)"),
    "bmw_e34_spec.zip": ("BMW 5 Series (E34)", "BMW 5 Series (E34)"),
    "bmw_e46.zip": ("BMW M3 (E46)", "BMW M3 GTR (E46)"),
    "bmw_g70_2024_2.0.zip": ("BMW 7 Series (G70)", "BMW 7 Series (G70)"),
    "bmw_m2_g87_modland.zip": ("BMW M2", "BMW M2 (G87)"),
    "bmw_m4.zip": ("BMW M4 (F82)", "BMW M4 (F82)"),
    "bmw_m4_g82.zip": ("BMW M4 (G82)", "BMW M4 (G82)"),
    "bmw_m5_f90_11_modland.zip": ("BMW M5 (F90)", "BMW M5 (F90)"),
    "bmw_m5f90_customv1.0.zip": ("BMW 5 Series (G30)", "BMW M5 (F90 / G30)"),
    "bmw_m6_f13_modland.zip": ("BMW 6 Series (F12)", "BMW M6 (F13)"),
    "bmw_x3.zip": ("BMW X3", "BMW X3"),
    "bmwe36_revamp_adamplg.zip": ("BMW 3 Series (E36)", "BMW 3 Series (E36)"),
    "bmwe53.zip": ("BMW X5 (E53)", "BMW X5 (E53)"),
    "bmwf10_modland.zip": ("BMW 5 Series (F10)", "BMW M5 (F10)"),
    "bmwg20_modland.zip": ("BMW 3 Series (G20)", "BMW 3 Series (G20)"),
    "bmwm3f80_modland.zip": ("BMW M3 (F80)", "BMW M3 (F80)"),
    "bmwx6m.zip": ("BMW X6", "BMW X6 M"),
    "bngtunerkijangkf10.zip": ("Toyota Kijang", "Toyota Kijang KF10"),
    "bronco.zip": ("Ford Bronco", "Ford Bronco"),
    "brx_mods_titanguincho_bng.zip": ("Volkswagen Titan", "Volkswagen Titan"),
    "brz86_unknown.zip": ("Toyota 86", "Toyota 86 / Subaru BRZ"),
    "bugatti_veyron_v2.zip": ("Bugatti Veyron", "Bugatti Veyron"),
    "buhanochka_by_staksal.zip": ("UAZ-452", "UAZ-452 Buhanka"),
    "bwr_pre-runner_tacoma_9b_gtmods.zip": ("Toyota Tacoma", "Toyota Tacoma PreRunner"),
    "cadillac_escalade_modland.zip": ("Cadillac Escalade", "Cadillac Escalade"),
    "carbonworks-beam-e-v3-20-0-37-x_1759505794_215703_performance_patch_v24_2023_by_neobeam_modland.zip": ("Spark-Renault SRT_01E", "Carbonworks Beam-E (Formula E)"),
    "cascadiakenemation.zip": ("Freightliner Cascadia", "Freightliner Cascadia"),
    "cayman_18.zip": ("Porsche 718 Boxster and Cayman", "Porsche 718 Cayman GT4 RS"),
    "chevrolet camaro 2024.zip": ("Chevrolet Camaro (sixth generation)", "Chevrolet Camaro 2024"),
    "chevy_silverado_2020_uae4.zip": ("Chevrolet Silverado", "Chevrolet Silverado 2020"),
    "chevyhighcountry.zip": ("Chevrolet Silverado", "Chevrolet Silverado High Country 2025"),
    "citroen_c2_by_dada-didi95903_1.1.zip": ("Citroën C2", "Citroën C2"),
    "citroensaxomk2 ukbeamng.zip": ("Citroën Saxo", "Citroën Saxo Mk2"),
    "citron_xsara_vts_by_dada-didi95903.zip": ("Citroën Xsara", "Citroën Xsara VTS"),
    "citysehvenny7_betarelease10__modland.zip": ("Honda City", "Honda City"),
    "cliomk2inc_modland.zip": ("Renault Clio", "Renault Clio Mk2 / V6"),
    "confused ferrari f40 v1.zip": ("Ferrari F40", "Ferrari F40"),
    "corvette c6.zip": ("Chevrolet Corvette (C6)", "Chevrolet Corvette C6"),
    "corvette c7 zr1.zip": ("Chevrolet Corvette (C7)", "Chevrolet Corvette C7 ZR1"),
    "crs_bmw_m4_g82_gt4.zip": ("BMW M4 GT4", "BMW M4 GT4 (G82)"),
    "dacia1310 r_modland.zip": ("Dacia 1300", "Dacia 1310"),
    "dacialoganmk1_hotfix.zip": ("Dacia Logan", "Dacia Logan Mk1"),
    "daciapack_kajto_fastlane.zip": ("Dacia Sandero", "Dacia Sandero"),
    "daciasandermk1_turbodiesel.zip": ("Dacia Sandero", "Dacia Sandero Mk1"),
    "daewoo-matiz.zip": ("Daewoo Matiz", "Daewoo Matiz"),
    "daewoo_tico.zip": ("Daewoo Tico", "Daewoo Tico"),
    "daihatsu-rocky-v1-0-0-35-x_1745087614_661509.zip": ("Daihatsu Rocky (A200)", "Daihatsu Rocky"),
    "dark horse.zip": ("Ford Mustang (seventh generation)", "Ford Mustang Dark Horse"),
    "ddc_ford_f250_modland.zip": ("Ford F-Series (sixth generation)", "1977 Ford F-250"),
    "docroswagge_as100_platform.zip": ("Toyota Corona", "Arima Caelo / Gaia (Corona EXiV)"),
    "docroswagge_cs200_platform.zip": ("Toyota Celica", "Arima Monica / Celina (Celica T200)"),
    "docroswagge_hestia.zip": ("Toyota Crown", "Arima Hestia (Toyota Crown)"),
    "dodge challenger.zip": ("Dodge Challenger", "Dodge Challenger"),
    "dodge_challenger_mmstudio.zip": ("Dodge Challenger", "Dodge Challenger"),
    "dodge_charger_14.zip": ("Dodge Charger (LX)", "2014 Dodge Charger"),
    "dodge_charger_2011-2014_fr999.zip": ("Dodge Charger (LX)", "Dodge Charger (2011-2014)"),
    "domestic_e60_2.0.zip": ("BMW M5 (E60)", "BMW M5 (E60)"),
    "duster24_modland.zip": ("Dacia Duster", "Dacia Duster"),
    "e39kenemationv14.zip": ("BMW 5 Series (E39)", "BMW 5 Series (E39)"),
    "e63s_modland.zip": ("Mercedes-Benz E-Class (W212)", "Mercedes-AMG E63S (W212)"),
    "elf_by_juniyani_modland.zip": ("Isuzu Elf", "Isuzu Elf"),
    "end_kei_van.zip": ("Suzuki Carry", "Daikisei Katai (Suzuki Every Kei Van)"),
    "estr34.zip": ("Nissan Skyline", "Nissan Skyline GT-R R34"),
    "f150_ww.zip": ("Ford F-150", "Ford F-150"),
    "f87bakebymealtyx.zip": ("BMW M2", "BMW M2 (F87)"),
    "f90bbnxmealtyxmods.zip": ("BMW M5 (F90)", "BMW M5 (F90)"),
    "feliup.zip": ("Škoda Felicia", "Škoda Felicia Pickup"),
    "ferf296gt3.zip": ("Ferrari 296 GTB", "Ferrari 296 GT3"),
    "ferrari_458_italia.zip": ("Ferrari 458", "Ferrari 458 Italia"),
    "ferrari_488_pista.zip": ("Ferrari 488", "Ferrari 488 Pista"),
    "fiat_ducato_fox.zip": ("Fiat Ducato", "Fiat Ducato"),
    "flanje_gr86.zip": ("Toyota 86", "Toyota GR86"),
    "ford gt.zip": ("Ford GT", "Ford GT"),
    "ford mustang cobra.zip": ("Ford Mustang SVT Cobra", "Ford Mustang Terminator Cobra"),
    "ford mustang gt 2013.zip": ("Ford Mustang (fifth generation)", "2013 Ford Mustang GT"),
    "ford-explorer_modland.zip": ("Ford Explorer", "2016 Ford Explorer"),
    "ford-gt-v4-75-0-37-x_1761245595_571877_overhaul_version_v16_2025_by_neobeam_modland.zip": ("Ford GT", "Ford GT (2017)"),
    "ford_fiesta_mk8by_loonzie_overhaul_update_v3.8_2024_by_engineeredmods.zip": ("Ford Fiesta", "Ford Fiesta Mk8"),
    "ford_ranger_modland.zip": ("Ford Ranger", "2021 Ford Ranger"),
    "ford_smax_fastlane_kajto.zip": ("Ford S-Max", "Ford S-MAX"),
    "ford_transit_2003.zip": ("Ford Transit", "2003 Ford Transit Mk6"),
    "fp_mobile_crane_130t_modland.zip": ("Liebherr mobile crane", "Grúa Móvil 130T"),
    "fr17_22.zip": ("Formula One car", "Formula Racecar FR22 (F1)"),
    "frosteezyspeed3_release.zip": ("Mazda3", "Mazdaspeed3 (BK)"),
    "frs200.zip": ("Ford RS200", "Ford RS200"),
    "fsw_vela.zip": ("Mazda MX-5 (ND)", "Procyon Vela (Mazda MX-5 ND)"),
    "fusion17_2017_v1.2_modland.zip": ("Ford Fusion (Americas)", "2017 Ford Fusion"),
    "g30_540i_.zip": ("BMW 5 Series (G30)", "BMW 540i (G30)"),
    "g_class_modland.zip": ("Mercedes-Benz G-Class", "Mercedes-Benz G-Class"),
    "gabry_celica_gt4_group_a.zip": ("Toyota Celica GT-Four", "Toyota Celica GT-Four ST205"),
    "gavril-scout-v1.4_overhaul_release_v3.0_2024_by_beamfixer.zip": ("Citroën Berlingo", "Gavril Scout (Berlingo/Kangoo)"),
    "gavril_corsum_modland.zip": ("Opel Corsa", "Gavril Corsum (Opel Corsa B)"),
    "gavril_sccw.zip": ("Spec Racer Ford", "Gavril SCCW Spec Racer"),
    "gavrile_tuning_update_v12_2024_by_tuninggarage_modland.zip": ("Ford Model T", "Gavril Model E (Ford Model T)"),
    "gazelle 3321 & 2705.zip": ("GAZelle", "GAZelle 3321 & 2705"),
    "gazelle3302.zip": ("GAZelle", "GAZ-3302 GAZelle"),
    "gazellenextnn tg m0dsbeamng.zip": ("GAZelle NEXT", "GAZelle NEXT"),
    "gniarmods_monza_branco_free_v2.zip": ("Chevrolet Monza (Brazil)", "Chevrolet Monza"),
    "golf_7_trix.zip": ("Volkswagen Golf Mk7", "Volkswagen Golf 7"),
    "gryaris_frosteezyedit.zip": ("Toyota GR Yaris", "Toyota GR Yaris"),
    "gsr-havalh6_dynamic_update_v21_2025_by_autobeam_modland.zip": ("Haval H6", "Haval H6"),
    "gt350.zip": ("Shelby Mustang", "Ford Mustang Shelby GT350"),
    "gtr_r35_v15_lbwk_modland.zip": ("Nissan GT-R", "Nissan GT-R R35 LBWK"),
    "hachiimpreza07.zip": ("Subaru Impreza", "Subaru Impreza 22B / GC8"),
    "henvenomf5.zip": ("Hennessey Venom F5", "Hennessey Venom F5"),
    "highlander25_spadie_remaster.zip": ("Toyota Grand Highlander", "Toyota Grand Highlander"),
    "himas9_alp_v1011.zip": ("Stelato S9", "Stelato S9"),
    "honda-integra-dc5-2.0.zip": ("Honda Integra", "Honda Integra DC5"),
    "honda_civic_type_r_pro.zip": ("Honda Civic Type R", "Honda Civic Type R (FL5)"),
    "hpmhptwo_pack_modland.zip": ("International Harvester Loadstar", "Gavril Heavystar II"),
    "hyundai i30n.zip": ("Hyundai i30", "Hyundai i30 N"),
    "inf21tahoe.zip": ("Chevrolet Tahoe", "Chevrolet Tahoe"),
    "inf_mercedes_gt_amg_tg_m0dsbeamng.zip": ("Mercedes-AMG GT", "Mercedes-AMG GT"),
    "inf_porsche_taycan.zip": ("Porsche Taycan", "Porsche Taycan"),
    "infcamarov2.zip": ("Chevrolet Camaro", "Chevrolet Camaro"),
    "inff150_modland.zip": ("Ford F-150", "Ford F-150"),
    "infgtr.zip": ("Nissan GT-R", "Nissan GT-R"),
    "infhuracan_modland_modland.zip": ("Lamborghini Huracán", "Lamborghini Huracán"),
    "infsilverado.zip": ("Chevrolet Silverado", "Chevrolet Silverado"),
    "inmx7m60i__beamng_paid_mods.zip": ("BMW X7", "BMW X7 M60i"),
    "jeep-cherokee-trailhawk-v4-14-0-37-x_1759865715_392498_advanced_build_v16_2025_by_beamfixer_modland.zip": ("Jeep Cherokee (KL)", "Jeep Cherokee Trailhawk"),
    "jeep_gladiator.zip": ("Jeep Gladiator (JT)", "Jeep Gladiator"),
    "jeep_grand_cherokee_zj.zip": ("Jeep Grand Cherokee (ZJ)", "Jeep Grand Cherokee ZJ"),
    "jeep_xj-mj.zip": ("Jeep Cherokee (XJ)", "Jeep Cherokee XJ / Comanche MJ"),
    "jerrdan.zip": ("Tow truck", "Jerr-Dan Grúa de Remolque"),
    "jerrdan_35.zip": ("Tow truck", "Jerr-Dan 35 Ton"),
    "jettaa5_fastlane_modland.zip": ("Volkswagen Jetta", "Volkswagen Jetta A5"),
    "jsd_fadx6m_v2.zip": ("BMW X6", "BMW X6 M"),
    "kalinahatch_v11_modland.zip": ("Lada Kalina", "Lada Kalina"),
    "kamaz4310.5350fix.zip": ("KamAZ-4310", "KamAZ-4310 / 5350"),
    "kamaz_43118.zip": ("KamAZ-43118", "KamAZ-43118"),
    "kamaz_54115_modland.zip": ("KamAZ-54115", "KamAZ-54115"),
    "kamaz_k5_fix_modland.zip": ("Kamaz-54901", "KamAZ K5 (54901)"),
    "kamazpack_alpha1_modland.zip": ("KamAZ-5320", "KamAZ 5320 / 5410 / 5511"),
    "kia_sportage_flanje.zip": ("Kia Sportage", "Kia Sportage"),
    "kicks21_spadie_v1.1_modland.zip": ("Nissan Kicks", "Nissan Kicks"),
    "koenigsegg_agera_inf_test1.zip": ("Koenigsegg Agera", "Koenigsegg Agera"),
    "koenigsegg_jesko_11.zip": ("Koenigsegg Jesko", "Koenigsegg Jesko"),
    "kraz25060ver10.zip": ("KrAZ-260", "KrAZ-250 / 260"),
    "kraz256ver1.5.zip": ("KrAZ-256", "KrAZ-256"),
    "l300_vibe_mods.zip": ("Mitsubishi Delica", "Mitsubishi L300 / Delica"),
    "lada 2114-2115 v1.4.zip": ("Lada Samara", "Lada 2114 / 2115"),
    "lamboaventadorbetav6.911.zip": ("Lamborghini Aventador", "Lamborghini Aventador"),
    "lamborghini aventador sjv new.zip": ("Lamborghini Aventador", "Lamborghini Aventador SVJ"),
    "lamborghini gallardo 2013.zip": ("Lamborghini Gallardo", "2013 Lamborghini Gallardo"),
    "lamborghini_sesto_elemento_v10_ultimate_patch_v34_2025_by_georgi_modland.zip": ("Lamborghini Sesto Elemento", "Lamborghini Sesto Elemento"),
    "lancer_evolution.zip": ("Mitsubishi Lancer Evolution", "Mitsubishi Lancer Evolution"),
    "lnavigator_bycherv.zip": ("Lincoln Navigator", "2020 Lincoln Navigator"),
    "lot49_beta_release.zip": ("Lotus 49", "Lotus Type 49"),
    "lot72d_release2_modland.zip": ("Lotus 72", "Lotus 72D"),
    "lotus_elise_mk3_v1_1_2_release.zip": ("Lotus Elise", "Lotus Elise Mk3"),
    "lotus_talbot_lkrl_mods_rework_by_dada-didi95903_1.2.zip": ("Talbot Sunbeam", "Talbot Sunbeam Lotus"),
    "lxr_x_flanje_c6_v1.3_modland.zip": ("Chevrolet Corvette (C6)", "Chevrolet Corvette C6"),
    "m3f80.zip": ("BMW M3 (F80)", "BMW M3 (F80)"),
    "m3g80-81.zip": ("BMW M3 (G80)", "BMW M3 (G80 / G81)"),
    "m4_xnme.zip": ("BMW M4 (G82)", "BMW M4 LCI (G82 / G83)"),
    "m5 e60 netrax.zip": ("BMW M5 (E60)", "BMW M5 (E60)"),
    "m7_charger13_modland.zip": ("Dodge Charger", "2013 Dodge Charger"),
    "m939_modland.zip": ("M939 series 5-ton 6x6 truck", "AM General M939 6x6"),
    "man_tgs.zip": ("MAN TGS", "MAN TGS Euro 6"),
    "man_tgx.zip": ("MAN TGX", "MAN TGX Euro 6"),
    "maz535_tissma_revamp_modland.zip": ("MAZ-535", "MAZ-535"),
    "mazda rx-7 (fd3s).zip": ("Mazda RX-7", "Mazda RX-7 (FD3S)"),
    "mazda-6-atenza by xwyrox_modland.zip": ("Mazda6", "Mazda 6 / Atenza"),
    "mazda-cosmo-sport.zip": ("Mazda Cosmo", "Mazda Cosmo Sport"),
    "mazda3.zip": ("Mazda3", "Mazda 3"),
    "mazda323familia.zip": ("Mazda Familia", "Mazda 323 Familia"),
    "mazda787b.zip": ("Mazda 787B", "Mazda 787B"),
    "mazda_miata.zip": ("Mazda MX-5", "Mazda MX-5 Miata"),
    "mazussrpack1.0.zip": ("MAZ-5337", "MAZ 5337 / 5432 / 5551"),
    "mbw218_modland.zip": ("Mercedes-Benz CLS-Class (W218)", "Mercedes-Benz CLS AMG (W218)"),
    "mclaren senna updated.zip": ("McLaren Senna", "McLaren Senna"),
    "mclaren-650s-fixed-0-36-x_1758387397_676396_pro_update_v3.0_2024_by_autobeam.zip": ("McLaren 650S", "McLaren 650S"),
    "mclaren-speedtail_modland.zip": ("McLaren Speedtail", "McLaren Speedtail"),
    "mclaren620r.zip": ("McLaren 620R", "McLaren 620R"),
    "mclaren765lt-jkingmaximan.zip": ("McLaren 765LT", "McLaren 765LT"),
    "mclaren7sportseries_frix.zip": ("McLaren 720S", "McLaren 720S / 765LT"),
    "megane_4_mrmrtdys_v3.0.zip": ("Renault Mégane", "Renault Mégane IV"),
    "meowcivic.zip": ("Honda Civic", "Honda Civic"),
    "mercedes benz amg gt series_phaien_v1.0_release.zip": ("Mercedes-AMG GT", "Mercedes-AMG GT"),
    "mercedes-benz c-class (w205) sedan.zip": ("Mercedes-Benz C-Class (W205)", "Mercedes-Benz C-Class (W205)"),
    "mercedes-benz c63s coupe.zip": ("Mercedes-Benz C-Class (W205)", "Mercedes-AMG C63S Coupé"),
    "mercedes-benz clase e (w214).zip": ("Mercedes-Benz E-Class (W214)", "Mercedes-Benz E-Class (W214)"),
    "mercedes-benz cls.zip": ("Mercedes-Benz CLS-Class (W219)", "Mercedes-Benz CLS (W219)"),
    "mercedes-benz g-class.zip": ("Mercedes-Benz G-Class", "Mercedes-Benz G-Class Brabus 900"),
    "mercedes-benz gle 2020.zip": ("Mercedes-Benz GLE", "2020 Mercedes-Benz GLE"),
    "mercedes-benz gls.zip": ("Mercedes-Benz GLS", "Mercedes-Benz GLS"),
    "mercedes-benz ml63.zip": ("Mercedes-Benz GLE", "Mercedes-Benz ML63 AMG"),
    "mercedes-benz s class w222.zip": ("Mercedes-Benz S-Class (W222)", "Mercedes-Benz S-Class (W222)"),
    "mercedes-benz s63 amg coupe.zip": ("Mercedes-Benz S-Class (C217)", "Mercedes-AMG S63 Coupé"),
    "mercedes-benz w211.zip": ("Mercedes-Benz E-Class (W211)", "Mercedes-Benz E-Class (W211)"),
    "mercedes-benz w223 2022.zip": ("Mercedes-Benz S-Class (W223)", "2022 Mercedes-Benz S-Class (W223)"),
    "mercedes_benz_w177_overhaul_build_v10_2023_by_autobeam_modland.zip": ("Mercedes-Benz A-Class (W177)", "Mercedes-Benz A-Class (W177)"),
    "mercedesr129final.zip": ("Mercedes-Benz SL-Class (R129)", "Mercedes-Benz SL (R129)"),
    "mestari_audi_rs4_b5_v1.zip": ("Audi RS 4", "Audi RS 4 (B5)"),
    "mf_toyota_fortuner.zip": ("Toyota Fortuner", "Toyota Fortuner"),
    "minicooper_f56_x_suff_modland.zip": ("Mini Hatch", "Mini Cooper (F56)"),
    "mitsubishi-evo-x-1.zip": ("Mitsubishi Lancer Evolution", "Mitsubishi Lancer Evo X"),
    "moskvich2140_pro_release_v12_2023_by_fastline_modland.zip": ("Moskvitch 2140", "Moskvich 2140"),
    "mtlfiretruck.zip": ("Fire engine", "MTL Fire Truck"),
    "multivan.zip": ("Volkswagen Transporter (T6)", "Volkswagen Multivan (T6)"),
    "mustang foxbody.zip": ("Ford Mustang (third generation)", "1993 Ford Mustang Cobra R Foxbody"),
    "mustang pack.zip": ("Ford Mustang", "Ford Mustang Pack"),
    "nexia.zip": ("Daewoo Nexia", "Daewoo Nexia"),
    "nexiarest_modland.zip": ("Daewoo Nexia", "Daewoo Nexia N150"),
    "nix_83_ranger_sas.zip": ("Ford Ranger", "1983 Ford Ranger SAS"),
    "nix_84_s10.zip": ("Chevrolet S-10", "1984 Chevy S-10"),
    "nix_97_dakota.zip": ("Dodge Dakota", "1997 Dodge Dakota"),
    "nix_chevy_k_series.zip": ("Chevrolet C/K", "Chevrolet K-Series"),
    "nix_jeep_brute.zip": ("Jeep Wrangler (JK)", "2010 Jeep Brute"),
    "nix_rock_bouncer.zip": ("Rock crawling", "Nix Rock Bouncer"),
    "nix_trail_raider.zip": ("Off-road vehicle", "Nix Trail Raider"),
    "notlow_eclipse_modland.zip": ("Mitsubishi Eclipse", "Mitsubishi Eclipse (2G)"),
    "octavia_v1.0_workers_group_modland.zip": ("Škoda Octavia (Typ 1U)", "Škoda Octavia (1U)"),
    "olympia26_spadie_v2.0.zip": ("Hyundai Kona", "Raevo Olympia Crossover"),
    "outback2020.zip": ("Subaru Outback", "2020 Subaru Outback"),
    "p1_release.zip": ("Citroën ZX", "Autron CVP (Citroën ZX)"),
    "palisade_v101.zip": ("Hyundai Palisade", "Hyundai Palisade"),
    "parolyokolpolo_modland.zip": ("Volkswagen Polo", "Volkswagen Polo"),
    "passat_b6_modland.zip": ("Volkswagen Passat (B6)", "Volkswagen Passat B6"),
    "patroljp.zip": ("Nissan Patrol", "Nissan Patrol 160"),
    "peugeot2008alg04000.zip": ("Peugeot 2008", "Peugeot 2008"),
    "peugeot205jp (1).zip": ("Peugeot 205", "Peugeot 205"),
    "peugeot308.zip": ("Peugeot 308", "2022 Peugeot 308"),
    "peugeot406final4.zip": ("Peugeot 406", "Peugeot 406"),
    "peugeotboxer.zip": ("Fiat Ducato", "2023 Peugeot Boxer"),
    "polo.zip": ("Volkswagen Polo", "Volkswagen Polo"),
    "pontiac g8.zip": ("Pontiac G8", "Pontiac G8"),
    "porsche 911 930.zip": ("Porsche 911 (930)", "Porsche 911 (930)"),
    "porsche 911 991.zip": ("Porsche 911 (991)", "Porsche 911 (991)"),
    "porsche 911 992.2 pcm update raz  more.zip": ("Porsche 911 (992)", "Porsche 911 (992)"),
    "porsche 911 997.zip": ("Porsche 911 (997)", "Porsche 911 (997)"),
    "porsche 911 gt2 rs.zip": ("Porsche 911 GT2", "Porsche 911 GT2 RS"),
    "porsche 911.zip": ("Porsche 911", "Porsche 911"),
    "porsche_cayenne_mmstudio.zip": ("Porsche Cayenne", "Porsche Cayenne"),
    "q8_andronisk_03-10-24.zip": ("Audi Q8", "Audi RS Q8"),
    "raiiiu_bentleybentaga.zip": ("Bentley Bentayga", "Bentley Bentayga"),
    "rangerover2022_modland.zip": ("Range Rover", "2022 Land Rover Range Rover"),
    "rc_wrangler_v2.0.zip": ("Jeep Wrangler (JL)", "2021 Jeep Wrangler"),
    "rcc_t-1000_roughcountrycrawling.zip": ("Trophy truck", "RCC T-1000 Crawler"),
    "redknee600ltv0_2b_modland.zip": ("McLaren 600LT", "McLaren 600LT"),
    "regera_frix_modland.zip": ("Koenigsegg Regera", "Koenigsegg Regera"),
    "renault megane.zip": ("Renault Mégane", "Renault Mégane II (X84)"),
    "renault21_b48_modland.zip": ("Renault 21", "Renault 21 (B48)"),
    "renault_5_turbo.zip": ("Renault 5 Turbo", "Renault 5 Turbo"),
    "renault_clio_williams_reworked_release_v23_2024_by_beamuploader_modland.zip": ("Renault Clio", "Renault Clio Williams"),
    "renault_kangoo_modland.zip": ("Renault Kangoo", "Renault Kangoo"),
    "renaultdacia-duster_1742472040_784370.zip": ("Nissan Terrano", "Renault Duster / Nissan Terrano"),
    "road runner.zip": ("Plymouth Road Runner", "Plymouth Road Runner"),
    "scirocco_fastlane.zip": ("Volkswagen Scirocco", "Volkswagen Scirocco"),
    "sea-t-leom-cupza-2022-sportline-edition_modland.zip": ("SEAT León", "2022 SEAT León Cupra"),
    "seat leon mk1.zip": ("SEAT León", "SEAT León Mk1 (1M)"),
    "sheik_mini_r50.zip": ("Mini Hatch", "Mini Cooper (R50)"),
    "sheike87fix.zip": ("BMW 1 Series (E87)", "BMW 1 Series (E87)"),
    "silveraado+ltz.zip": ("Chevrolet Silverado", "Chevrolet Silverado 2500HD LTZ"),
    "sksuperb2_fastlane_performance_update_v26_2025_by_autobeam_modland.zip": ("Škoda Superb", "Škoda Superb II"),
    "skylime polo.zip": ("Volkswagen Polo", "Volkswagen Polo"),
    "sorento25_spadie_modland.zip": ("Kia Sorento", "2025 Kia Sorento"),
    "spark2021.zip": ("Chevrolet Spark", "2021 Chevrolet Spark"),
    "stiv_miovi_stella.zip": ("Dacia SuperNova", "Miovi Stella (Dacia SuperNova)"),
    "subaru_wrx_sti_2004_kthree.zip": ("Subaru Impreza WRX STI", "2004 Subaru Impreza WRX STI"),
    "suzuki-swift-2004-2010-v1-7-0-35-x_1746736758_848969.zip": ("Suzuki Swift", "Suzuki Swift (2004-2010)"),
    "t4runnertrdpro.zip": ("Toyota 4Runner", "Toyota 4Runner TRD Pro"),
    "takumi_subaru impreza wrx hatch.zip": ("Subaru Impreza", "Subaru Impreza WRX Hatch"),
    "tlc 200 & tg_m0dsbeamng.zip": ("Toyota Land Cruiser (J200)", "Toyota Land Cruiser 200"),
    "tow_truck_sprinter.zip": ("Mercedes-Benz Sprinter", "Gavril Vianter Grúa (Sprinter)"),
    "toyota-land-cruiser-fj55.zip": ("Toyota Land Cruiser (J50)", "Toyota Land Cruiser FJ55"),
    "toyota_camry_2007.zip": ("Toyota Camry", "2007 Toyota Camry"),
    "toyota_fortuner_modland.zip": ("Toyota Fortuner", "Toyota Fortuner"),
    "toyota_land_cruiser.zip": ("Toyota Land Cruiser (J60)", "Toyota Land Cruiser 60 Series"),
    "toyota_land_cruiser_300.zip": ("Toyota Land Cruiser (J300)", "Toyota Land Cruiser 300"),
    "toyota_land_cruiser_fj45.zip": ("Toyota Land Cruiser (J40)", "Toyota Land Cruiser FJ45"),
    "toyotahiluxv2.01.zip": ("Toyota Hilux", "Toyota Hilux"),
    "transit.zip": ("Ford Transit", "Ford Transit Mk6"),
    "transporter_mods.zip": ("Volkswagen Transporter (T5)", "Volkswagen Transporter (T5)"),
    "ttnkiafortekoup.zip": ("Kia Forte", "Kia Forte Koup"),
    "ttnporschecarreragt.zip": ("Porsche Carrera GT", "Porsche Carrera GT (980)"),
    "tundra_evolvetech_modland.zip": ("Toyota Tundra", "Toyota Tundra TRD"),
    "ty_rolls_royce_cullinan_v1.0.zip": ("Rolls-Royce Cullinan", "Rolls-Royce Cullinan"),
    "uaz-31514.zip": ("UAZ-469", "UAZ-31514"),
    "uaz-469-1962.zip": ("UAZ-469", "1962 UAZ-469"),
    "unicera_truck_kun.zip": ("Mitsubishi Fuso Canter", "Unicera Truck-kun (Fuso Canter)"),
    "unlimitedfh.zip": ("Volvo FH", "Volvo FH12"),
    "ural_ivannq_0.39.4.zip": ("Ural-4320", "Ural 4320-31"),
    "v_1_01_tgr2020_remods.zip": ("Toyota Supra", "Toyota GR Supra (A90)"),
    "vaz 2108-21099_viharekmods.zip": ("Lada Samara", "VAZ 2108 / 2109 / 21099"),
    "vaz2106relatedv4kenemation.zip": ("Lada 1500", "VAZ-2106"),
    "vestakenemationv2.zip": ("Lada Vesta", "Lada Vesta"),
    "viper_revamped_modland.zip": ("Dodge Viper", "Dodge Viper"),
    "volkswagen gol g2 v4 - verso completa.zip": ("Volkswagen Gol", "Volkswagen Gol G2"),
    "volkswagen saveiro g8 ar5.zip": ("Volkswagen Saveiro", "Volkswagen Saveiro G8"),
    "volkswagen-jetta-mk3-0-37-x_1759505638_284654_overhaul_edition_v13_2024_by_georgi_modland.zip": ("Volkswagen Jetta", "Volkswagen Jetta Mk3"),
    "volkswagen-sharan-2016-v1-2-0-36-x_1753730730_980404_advanced_update_v1.9_2024_by_prodrive.zip": ("Volkswagen Sharan", "2016 Volkswagen Sharan"),
    "volkswagen_golf_mk4.zip": ("Volkswagen Golf Mk4", "Volkswagen Golf Mk4"),
    "volkswagen_polo_mk5.zip": ("Volkswagen Polo", "Volkswagen Polo Mk5"),
    "volkswagen_tcross_v1.8.zip": ("Volkswagen T-Cross", "Volkswagen T-Cross"),
    "volvo xc90 20152019.zip": ("Volvo XC90", "Volvo XC90"),
    "volvo240.zip": ("Volvo 200 Series", "Volvo 240"),
    "vw golf mk1 germanracing.zip": ("Volkswagen Golf Mk1", "Volkswagen Golf Mk1"),
    "vw golf mk2 germanracing.zip": ("Volkswagen Golf Mk2", "Volkswagen Golf Mk2"),
    "vw golf mk3 germanracing.zip": ("Volkswagen Golf Mk3", "Volkswagen Golf Mk3"),
    "vw golf mk4 germanracing.zip": ("Volkswagen Golf Mk4", "Volkswagen Golf Mk4"),
    "vw golf mk6 germanracing.zip": ("Volkswagen Golf Mk6", "Volkswagen Golf Mk6"),
    "w164kenemationv2.zip": ("Mercedes-Benz M-Class", "Mercedes-Benz ML (W164)"),
    "w203kenemationv4.zip": ("Mercedes-Benz C-Class (W203)", "Mercedes-Benz C-Class (W203)"),
    "western_star_57x_advanced_release_v10_2023_by_autobeam_modland.zip": ("Western Star 5700", "Western Star 57X"),
    "wscx_prerunner_bronco_modland.zip": ("Ford Bronco", "Ford Bronco PreRunner"),
    "x55_pro.zip": ("Chery Tiggo 5x", "MVM X55 Pro"),
    "x5mrest.zip": ("BMW X5", "BMW X5 M (F95)"),
    "xm_betarelease.zip": ("BMW XM", "BMW XM"),
    "zil130ver1.0.zip": ("ZIL-130", "ZiL-130"),
    "zis_110.zip": ("ZIS-110", "ZIS-110"),
    "zomvl_nolimits_chevrolet_lumina_2008-2010.zip": ("Holden Commodore (VE)", "Chevrolet Lumina (2008-2010)"),
    # Repo lore-friendly cars
    "autobello_minilena.zip": ("Fiat 600", "Autobello Minilena (Fiat 600)"),
    "awbete_adamplg.zip": ("Volkswagen Polo Mk2", "AW Bete (VW Polo 86C)"),
    "bcnz_tango_v10.zip": ("Renault Twingo", "Cherrier Tango (Renault Twingo)"),
    "bitron_b2.zip": ("Citroën BX", "Bitron B2 (Citroën BX)"),
    "bug-aw-type1.zip": ("Volkswagen Beetle", "AW Type 1 Bug (VW Beetle)"),
    "burn48_repo.zip": ("1949 Ford", "Burnside AeroCoupe"),
    "claria.zip": ("Nissan Cedric", "1976 Ibishu Claria"),
    "cseries_shoe_vibe.zip": ("BMW 6 Series (E63)", "ETK C-Series"),
    "dazy_satsuma_amp.zip": ("Nissan Cherry", "Satsuma 1000 (Datsun 100A)"),
    "enix.zip": ("Chevrolet Express", "Gavril Enix"),
    "etka.zip": ("Volkswagen Golf Mk1", "AW Astro (Golf Mk1)"),
    "etkk_lucasbe.zip": ("BMW 8 Series (E31)", "1994 ETK K-Series"),
    "etkluxe_repo.zip": ("BMW 7 Series (G11)", "ETK 900-Series"),
    "evvan_ch.zip": ("Dodge Ram Van", "Bruckell ECV"),
    "ffe-motorsports_v10-35sp-blijo.zip": ("McLaren MP4/6", "FFE-Motorsports V10-35SP"),
    "fsw_fullsizesuv.zip": ("Lexus LX", "2022 Procyon Centauri (Lexus LX)"),
    "goal.zip": ("Volkswagen Gol", "AW Goal (VW Gol)"),
    "gunner_demo.zip": ("Hummer H1", "Gunner Patriot / Claymore"),
    "kashira2electricboogaloo.zip": ("Toyota Previa", "1995 Ibishu Kashira Gen 2"),
    "kashiralegacy.zip": ("Mitsubishi Chariot", "1989 Ibishu Kashira Gen 1"),
    "kevo_the_third.zip": ("Suzuki Carry", "Ibishu Kevin Kei Truck"),
    "one_naguluna.zip": ("Fiat Uno", "Fait One (Fiat Uno)"),
    "picnicdemo_lucasbe.zip": ("Peugeot 106", "1992 Cherrier Picnic (Peugeot 106)"),
    "ryancookie_taz.zip": ("Lada Riva", "TAZ Baikal / Mir (Lada)"),
    "satsuma210_by_mike94.zip": ("Datsun Bluebird", "1958 Satsuma 210"),
    "serenity.zip": ("Toyota Century", "1984 Ibishu Serenity"),
    "shima.zip": ("Honda Beat", "Ibishu Shima (Honda Beat)"),
    "soliad_ventera.zip": ("Pontiac Firebird", "Soliad Ventera (Firebird)"),
    "spmfun.zip": ("Polaris RZR", "Super Powers Mobility EPEX"),
    "thw_ccf2.zip": ("Mazda MX-5 (ND)", "2020 Hirochi CCF (MX-5 ND)"),
    "tpulackpoolsuperlite.zip": ("Caterham 7", "Blackpool Superlite"),
    "tpublackpoolsuperlite.zip": ("Caterham 7", "Blackpool Superlite"),
    "tpufjunior.zip": ("Formula Junior", "Formula Ibishu"),
    "tpuformulabee.zip": ("Formula Vee", "Formula Bee"),
    "trackfabautobellobuggy.zip": ("Baja Bug", "Trackfab Dune Hopper"),
    "z31.zip": ("Nissan 300ZX", "1980s Ibishu 300BX (Nissan 300ZX Z31)"),
}

# Real-world maps dictionary: zip_lower -> (display_name, wiki_title, real_location_label)
REAL_MAPS_MAP = {
    "2k-ashinoko.zip": ("Ashinoko Skyline", "Lake Ashi", "Lago Ashi, Hakone, Japón"),
    "2k-irohazaka_performance_build_v3.6_2024_by_tuninggarage.zip": ("Irohazaka", "Irohazaka", "Irohazaka, Nikkō, Japón"),
    "2k-momiji_modland.zip": ("Momiji Line", "Nikkō, Tochigi", "Momiji Line, Nikkō, Japón"),
    "2k-nagao_reworked_release_v39_2024_by_beamfixer_modland.zip": ("Nagao Pass", "Hakone, Kanagawa", "Paso de Nagao, Hakone, Japón"),
    "2k-sadamine.zip": ("Sadamine Pass", "Chichibu, Saitama", "Paso de Sadamine, Saitama, Japón"),
    "2k-tsuchisaka.zip": ("Tsuchisaka Pass", "Chichibu, Saitama", "Paso de Tsuchisaka, Gunma, Japón"),
    "2k-turnpike_ultimate_build_v2.6_2025_by_beamuploader.zip": ("Hakone Turnpike", "Hakone Turnpike", "Hakone Turnpike, Kanagawa, Japón"),
    "2k-yabitsu_optimized_patch_v3.3_2025_by_beamuploader.zip": ("Yabitsu Pass", "Mount Ōyama (Kanagawa)", "Paso de Yabitsu, Kanagawa, Japón"),
    "60s_lemans1point1.zip": ("60s Le Mans (Circuit de la Sarthe)", "Circuit de la Sarthe", "Le Mans, Francia"),
    "beamng-11987.zip": ("El Tambo (MapToPlay)", "Manizales", "El Tambo / Manizales, Caldas, Colombia"),
    "bolivianroadsbydino12507.zip": ("Bolivian Roads (Camino de las Yungas)", "Yungas Road", "Camino de las Yungas, Bolivia"),
    "buzludzha_modfan.zip": ("Buzludzha Pass", "Buzludzha", "Monumento de Buzludzha, Bulgaria"),
    "cadwell1point2.zip": ("Cadwell Park", "Cadwell Park", "Lincolnshire, Reino Unido"),
    "caney_ridge_16k.zip": ("Caney Ridge, USA", "Appalachian Mountains", "Caney Ridge, Apalaches, EE. UU."),
    "dealsgap.zip": ("Tail of the Dragon / Deal's Gap", "Deals Gap, North Carolina", "US-129 Deal's Gap, EE. UU."),
    "fakotor-trojica_modland.zip": ("Kotor - Trojica Hillclimb", "Kotor", "Kotor - Trojica, Montenegro"),
    "happogahara.zip": ("Happogahara Touge", "Nasu, Tochigi", "Happogahara, Tochigi, Japón"),
    "kamurocho_judgment_am5.zip": ("Kamurocho (Kabukicho)", "Kabukicho", "Kabukicho, Shinjuku, Tokio, Japón"),
    "kasach_desert.zip": ("Desierto de Kazajistán", "Kyzylkum Desert", "Kazajistán"),
    "ks_nord_v20231124_v2.zip": ("Nürburgring Nordschleife", "Nürburgring", "Nürburg, Alemania"),
    "lemans26_tunim.zip": ("Circuit de la Sarthe (Le Mans)", "Circuit de la Sarthe", "Le Mans, Francia"),
    "magadan_modland.zip": ("Magadan Oblast", "Magadan Oblast", "Óblast de Magadán, Rusia"),
    "miami_city_real_world_-_remastered_tuning_version_v13_2023_by_prodrive_modland.zip": ("Miami City", "Miami", "Miami, Florida, EE. UU."),
    "monaco_tunim.zip": ("Circuit de Monaco", "Circuit de Monaco", "Montecarlo, Mónaco"),
    "mountpanorama12htunim.zip": ("Mount Panorama Circuit", "Mount Panorama Circuit", "Bathurst, Australia"),
    "nevada_interstate_openbeta.zip": ("Nevada Interstate", "Interstate 80 in Nevada", "Nevada, EE. UU."),
    "norwegian_backroads_152_ reshjemheia.zip": ("Reshjemheia (Norwegian Backroads)", "Telemark", "Reshjemheia, Telemark, Noruega"),
    "osaka.zip": ("Sotenbori (Dōtonbori, Osaka)", "Dōtonbori", "Osaka, Japón"),
    "passostelvio.zip": ("Passo dello Stelvio", "Stelvio Pass", "Paso del Stelvio, Italia"),
    "pikespeak.zip": ("Pikes Peak (LIDAR Edition)", "Pikes Peak", "Pikes Peak, Colorado, EE. UU."),
    "priozersk tg_koeno102rp.zip": ("Priozersk", "Priozersk", "Priozersk, Rusia"),
    "schneeweg_grille.zip": ("Schneeberg", "Schneeberg, Saxony", "Schneeberg, Sajonia, Alemania"),
    "sexdrega_sweden_map_modland.zip": ("Sexdrega, Sweden", "Sexdrega", "Sexdrega, Suecia"),
    "sgh1.5.zip": ("Sangerhausen", "Sangerhausen", "Sangerhausen, Sajonia-Anhalt, Alemania"),
    "skeleton_coast.zip": ("Skeleton Coast", "Skeleton Coast", "Costa de los Esqueletos, Namibia"),
    "south_east_sahara__map(offroad)_modland.zip": ("South East Sahara (12.77°N, 17.61°E)", "Sahara", "Desierto del Sahara, Chad"),
    "the_gap.zip": ("The Gap (Southern Appalachia)", "Blue Ridge Mountains", "Apalaches del Sur, EE. UU."),
    "three_passes_v093_small_modland.zip": ("Three Passes (Grimsel / Furka / Susten)", "Susten Pass", "Alpes Suizos, Suiza"),
    "tokyo.zip": ("C1 Tokyo Expressway (Shutokō)", "Shuto Expressway", "Tokio, Japón"),
    "twinringbyjosh_modland.zip": ("Twin Ring Motegi", "Mobility Resort Motegi", "Motegi, Tochigi, Japón"),
    "veincalif10.zip": ("California Highway (PCH)", "California State Route 1", "Big Sur / Santa Bárbara, California"),
    "xwtarragona.zip": ("Tarragona Street", "Tarragona", "Tarragona, España"),
    "yokohama.zip": ("Yokohama (Isezakicho)", "Yokohama", "Yokohama, Kanagawa, Japón"),
    "dardsesterobeachshortcourse.zip": ("Estero Beach Short Course", "Ensenada, Baja California", "Estero Beach, Baja California, México"),
    "dardsglenhelenraceway.zip": ("Glen Helen Raceway", "San Bernardino, California", "San Bernardino, California, EE. UU."),
    "dardslakeelsinoremotorsportspark.zip": ("Lake Elsinore Motorsports Park", "Lake Elsinore, California", "Lake Elsinore, California, EE. UU."),
    "dardslasvegasspeedway-offroad.zip": ("Las Vegas Motor Speedway (Offroad)", "Las Vegas Motor Speedway", "Las Vegas, Nevada, EE. UU."),
    "dardslucasoilsspeedway.zip": ("Lucas Oil Speedway", "Lucas Oil Speedway", "Wheatland, Missouri, EE. UU."),
    "dardslucasoilspeedway.zip": ("Lucas Oil Speedway", "Lucas Oil Speedway", "Wheatland, Missouri, EE. UU."),
    "dousojintouge.zip": ("Dousojin Touge", "Mount Tsukuba", "Paso Dousojin, Ibaraki, Japón"),
    "grille_autobahn_loop.zip": ("Autobahn 57k", "Autobahn", "Autobahn, Alemania"),
    "mbwr_alps.zip": ("Swiss Alps (MBWR)", "Swiss Alps", "Alpes Suizos, Suiza"),
    "mount_coottha.zip": ("Mount Coot-tha", "Mount Coot-tha", "Brisbane, Queensland, Australia"),
    "mount_glorious.zip": ("Mount Glorious", "Mount Glorious, Queensland", "Queensland, Australia"),
    "mulholland_v092b_hotfix.zip": ("Mulholland Drive", "Mulholland Drive", "Los Ángeles, California, EE. UU."),
    "myherin_main.zip": ("Myherin Rally Stage", "Cambrian Mountains", "Myherin, Gales, Reino Unido"),
    "nefr_0391.zip": ("New England Forest Rally", "Newry, Maine", "Maine, Nueva Inglaterra, EE. UU."),
    "nissering.zip": ("Nisseringen (55.22°N, 11.90°E)", "Næstved", "Nisseringen, Næstved, Dinamarca"),
    "otarumi_touge_v1.zip": ("Otarumi Touge", "Mount Takao", "Paso Otarumi, Tokio/Kanagawa, Japón"),
    "rutas2.zip": ("Argentinean Roads (Rutas Argentinas)", "Ruta Nacional 40 (Argentina)", "Rutas de Argentina"),
    "rydal_039_fix.zip": ("Rydal, Australia", "Rydal, New South Wales", "Rydal, Nueva Gales del Sur, Australia"),
    "sanok_repo.zip": ("DK28 Wujskie - Tyrawa Wołoska", "Sanok", "Sanok, Podcarpacia, Polonia"),
    "shasta_deploy_260713.zip": ("Mount Shasta", "Mount Shasta", "Monte Shasta, California, EE. UU."),
    "somerset1_9.zip": ("Somerset, UK", "Somerset", "Somerset, Inglaterra, Reino Unido"),
    "tbd_newport_speedway_rally.zip": ("Newport Speedway", "Newport, Tennessee", "Newport, Tennessee, EE. UU."),
    "nanamagari.zip": ("Nanamagari Touge", "Hakone, Kanagawa", "Nanamagari, Kanagawa, Japón"),
}

# Explicit Wikimedia Commons photo queries for real-world maps whose Wikipedia article
# lead image is a track diagram, highway shield, flag, painting, or satellite raster.
MAP_COMMONS_PHOTO_QUERIES = {
    "2k-irohazaka_performance_build_v3.6_2024_by_tuninggarage.zip": "Irohazaka Nikko",
    "2k-momiji_modland.zip": "Lake Chuzenji Nikko",
    "60s_lemans1point1.zip": "Circuit de la Sarthe Le Mans track",
    "lemans26_tunim.zip": "24 Hours of Le Mans race circuit",
    "bolivianroadsbydino12507.zip": "Yungas Road Bolivia",
    "cadwell1point2.zip": "Cadwell Park race circuit",
    "kasach_desert.zip": "Kazakhstan steppe landscape",
    "ks_nord_v20231124_v2.zip": "Nordschleife Nurburgring track",
    "magadan_modland.zip": "Kolyma Magadan Oblast landscape",
    "monaco_tunim.zip": "Monaco Grand Prix street circuit",
    "mountpanorama12htunim.zip": "Mount Panorama Bathurst circuit",
    "nevada_interstate_openbeta.zip": "Interstate 80 Nevada desert highway",
    "schneeweg_grille.zip": "Schneeberg Sachsen Germany",
    "south_east_sahara__map(offroad)_modland.zip": "Sahara sand dunes Morocco",
    "tokyo.zip": "Shuto Expressway Tokyo night",
    "twinringbyjosh_modland.zip": "Twin Ring Motegi 2010",
    "veincalif10.zip": "Bixby Creek Bridge Big Sur coast",
    "dardslasvegasspeedway-offroad.zip": "Las Vegas Motor Speedway track",
    "dardslucasoilspeedway.zip": "Dirt track racing oval",
    "dardslucasoilsspeedway.zip": "Dirt track racing oval",
    "dardsglenhelenraceway.zip": "San Bernardino Mountains California",
    "grille_autobahn_loop.zip": "Bundesautobahn A3 Germany",
    "mbwr_alps.zip": "Julier Pass Switzerland road",
    "mulholland_v092b_hotfix.zip": "Mulholland Drive Los Angeles hills",
    "skeleton_coast.zip": "Skeleton Coast Namibia dunes",
    "rydal_039_fix.zip": "Blue Mountains New South Wales valley",
    "rutas2.zip": "Ruta Nacional 40 Argentina Patagonia",
}

FICTIONAL_DISPLAY_OVERRIDES = {
    "russianprovincetown.zip": "Russian Province Town",
    "popcorn_modland.zip": "Dangerous Roads 2 - Sierra Mexicana",
    "maju.zip": "Dowon Island (Guljin County)",
    "kamus.zip": "Lost Paradise",
    "run.zip": "Seaside Roads",
    "domikvderevne 1.0.zip": "Domik v Derevne (Home to Village)",
    "africantrails.zip": "African Trails",
    "gniar_br_costa_oeste.zip": "Brasil Long Trip 100km+",
    "gtasa_sf.zip": "GTA San Andreas - San Fierro",
    "gtasanandreasv22_modland.zip": "GTA San Andreas Map",
    "los_santos_gta_v.zip": "GTA V - Los Santos",
    "liberty_city_fullv2.zip": "GTA IV - Liberty City",
    "polish_roads_repo.zip": "Polish Roads (Cebulowo)",
    "ms01_modland.zip": "Mediterranean Special Stage 01",
    "uralsk1.2.zip": "Uralsk (Fictional Sverdlovsk)",
    "ussrproject_remap_beta_modland.zip": "USSR Project REMAP",
    "1toxict63es50.zip": "Toxic Sand Dunes",
    "80s_racing.zip": "1980s Historic Hirochi Raceway",
    "bifdro_map.zip": "Rocky Coast, USA",
    "tbd_rallycross_mod.zip": "Track's Rallycross Pack",
    "sierra_summit.zip": "Sierra Summit Raceway",
    "relentless_rally75.zip": "Relentless Rally (30.8km)",
}

TRUCK_ZIPS = {
    "brx_mods_titanguincho_bng.zip", "cascadiakenemation.zip", "elf_by_juniyani_modland.zip",
    "fp_mobile_crane_130t_modland.zip", "hpmhptwo_pack_modland.zip", "jerrdan.zip",
    "jerrdan_35.zip", "kamaz4310.5350fix.zip", "kamaz_43118.zip", "kamaz_54115_modland.zip",
    "kamaz_k5_fix_modland.zip", "kamazpack_alpha1_modland.zip", "kraz25060ver10.zip",
    "kraz256ver1.5.zip", "m939_modland.zip", "man_tgs.zip", "man_tgx.zip",
    "maz535_tissma_revamp_modland.zip", "mazussrpack1.0.zip", "mtlfiretruck.zip",
    "unicera_truck_kun.zip", "unlimitedfh.zip", "ural_ivannq_0.39.4.zip",
    "western_star_57x_advanced_release_v10_2023_by_autobeam_modland.zip", "zil130ver1.0.zip",
}

BAD_IMG_WORDS = (
    "heightmap", "depth", "layermap", "holemap", "terrainpreset", "null_",
    "_n.", "_nm.", "_r.", "_ao.", "_b.", "_h.", "rough", "normal", "mask",
    "roadmap", "minimap", "template_preview", "granturismo.png",
    "myherin_main_preview.png", "shasta_preview.jpg", "ev_charger",
    "fuel_local", "fuel_nodeoline", "jp_evs", "annotation",
)

NON_PHOTO_URL_TOKENS = (
    "logo", "flag", "map", "sign", "zeichen", "shield", "badge", "emblem",
    "gradient", "diagram", "plant", "brigade", "detall", "_in_erz",
    "region_of_", "1px-250m", "real_color", "overview", "coat_of_arms",
    "emblema", "escudo", "karte", "carte", "mappa", "chart", "icon",
    "wordmark", "silhouette", "blueprint", "schema", "drawing",
    "illustration", "stamp", "poster", "20101003_daewoo_lemans_1",
    "helicopter", "otavi_1945", "xp2002_leads_wt28", "sanbernardinostation",
    "page1-", "page2-", "stereoscope", "argentopyrite", "convoy,_27_march_1945",
    "sts0", "iss0", "flora_of_japan", "model_car", "diecast", "veritas_rs",
)

CAR_DETAIL_RE = re.compile(
    r"(?:^|[_\-\s,(])(rear|heck|taillight|headlight|interior|cockpit|dashboard|steering|engine|motorraum|wheel|rim|alloy|tire|tyre|closeup|close-up|trunk|boot|seat|seats|dash|speedo|odometer)(?:$|[_\-\s,).])",
    re.IGNORECASE,
)

def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    h = hashlib.md5(text.encode("utf-8")).hexdigest()[:6]
    return f"{s[:45]}-{h}"

def load_lenient_json(raw: bytes):
    text = raw.decode("utf-8-sig", errors="replace")
    try:
        return json.loads(text)
    except Exception:
        text2 = re.sub(r"//.*?$", "", text, flags=re.MULTILINE)
        text2 = re.sub(r",\s*([}\]])", r"\1", text2)
        try:
            return json.loads(text2)
        except Exception:
            return None

def get_image_metrics(raw_bytes: bytes):
    try:
        with Image.open(io.BytesIO(raw_bytes)) as im:
            w, h = im.size
            rgb = im.convert("RGB")
            stat = ImageStat.Stat(rgb)
            mean_b = sum(stat.mean) / 3.0
            std_b = sum(stat.stddev) / 3.0
            small = rgb.resize((64, 64))
            raw_px = small.tobytes()
            total_px = 64 * 64
            whites = 0
            blacks = 0
            for idx in range(0, len(raw_px), 3):
                r, g, b = raw_px[idx], raw_px[idx + 1], raw_px[idx + 2]
                if r > 235 and g > 235 and b > 235:
                    whites += 1
                elif r < 16 and g < 16 and b < 16:
                    blacks += 1
            return {
                "width": w,
                "height": h,
                "mean": mean_b,
                "std": std_b,
                "white_ratio": whites / total_px,
                "black_ratio": blacks / total_px,
            }
    except Exception:
        return None

def is_good_game_preview(raw_bytes: bytes, min_width: int = 360) -> bool:
    m = get_image_metrics(raw_bytes)
    if not m:
        return False
    return (
        m["width"] >= min_width
        and m["height"] >= 150
        and m["std"] >= 30.0
        and 22.0 <= m["mean"] <= 215.0
        and m["white_ratio"] <= 0.42
        and m["black_ratio"] <= 0.55
    )

def save_resized_jpeg(raw_bytes: bytes, out_path: Path, max_w: int, quality: int):
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        if img.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", img.size, (24, 24, 27))
            rgba = img.convert("RGBA")
            bg.paste(rgba, mask=rgba.split()[3])
            img = bg
        else:
            img = img.convert("RGB")
        if img.width > max_w:
            ratio = max_w / float(img.width)
            img = img.resize((max_w, max(1, int(img.height * ratio))), Image.Resampling.LANCZOS)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path, format="JPEG", quality=quality, optimize=True)
        return (img.width, img.height)
    except Exception:
        return None

def render_relief_from_heightmap(raw_bytes: bytes, out_path: Path):
    """Generates a shaded 16:9 topographic relief JPEG from a terrain heightmap."""
    try:
        with Image.open(io.BytesIO(raw_bytes)) as src:
            gray = src.convert("L").resize((640, 360), Image.Resampling.BILINEAR)
        # NW directional lighting via simple shifted difference
        dx = ImageChops.subtract(gray, ImageChops.offset(gray, 2, 0), scale=1, offset=128)
        dy = ImageChops.subtract(gray, ImageChops.offset(gray, 0, 2), scale=1, offset=128)
        shade = ImageChops.blend(dx, dy, 0.5)
        r_ch = ImageChops.blend(gray, shade, 0.48).point(lambda v: max(35, min(225, int(v * 0.72 + 48))))
        g_ch = ImageChops.blend(gray, shade, 0.48).point(lambda v: max(45, min(230, int(v * 0.78 + 56))))
        b_ch = ImageChops.blend(gray, shade, 0.48).point(lambda v: max(40, min(220, int(v * 0.68 + 46))))
        out_img = Image.merge("RGB", (r_ch, g_ch, b_ch))
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_img.save(out_path, format="JPEG", quality=80, optimize=True)
        return out_img.size
    except Exception:
        return None

def gather_map_preview_candidates(names, lvl_dirs, lvl_infos):
    primary = []
    modinfo_imgs = []
    secondary = []

    for d in lvl_dirs:
        info = lvl_infos.get(d) or {}
        for prev in (info.get("previews") or []):
            cand = f"levels/{d}/{prev}".lower()
            for n in names:
                nl = n.lower()
                if nl == cand and nl.endswith((".jpg", ".jpeg", ".png", ".webp")):
                    if not any(b in nl for b in BAD_IMG_WORDS):
                        primary.append(n)
    for d in lvl_dirs:
        prefix = f"levels/{d}/".lower()
        for n in names:
            nl = n.lower()
            if nl.startswith(prefix) and nl.endswith((".jpg", ".jpeg", ".png", ".webp")):
                rel = nl[len(prefix):]
                if "/" not in rel and ("preview" in rel or rel.startswith("default.")) and not any(b in nl for b in BAD_IMG_WORDS):
                    if n not in primary:
                        primary.append(n)
    for n in names:
        nl = n.lower()
        if nl.startswith("mod_info/") and "/images/" in nl and nl.endswith((".jpg", ".jpeg", ".png", ".webp")):
            modinfo_imgs.append(n)
    for n in names:
        nl = n.lower()
        if nl.startswith("mod_info/") and "/thumbs/" in nl and nl.endswith((".jpg", ".jpeg", ".png", ".webp")):
            if n not in modinfo_imgs:
                modinfo_imgs.append(n)
    for d in lvl_dirs:
        prefix = f"levels/{d}/quickrace/".lower()
        for n in names:
            nl = n.lower()
            if nl.startswith(prefix) and nl.endswith((".jpg", ".jpeg", ".png", ".webp")):
                secondary.append(n)
    for d in lvl_dirs:
        prefix = f"levels/{d}/".lower()
        for n in names:
            nl = n.lower()
            if nl.startswith(prefix) and nl.endswith((".jpg", ".jpeg", ".png", ".webp")):
                rel = nl[len(prefix):]
                if "/" not in rel and not any(b in nl for b in BAD_IMG_WORDS):
                    if n not in primary and n not in secondary:
                        secondary.append(n)

    # Combine while preserving preference order
    return primary, modinfo_imgs, secondary

def pick_best_map_preview(zf: zipfile.ZipFile, names, lvl_dirs, lvl_infos, out_path: Path):
    primary, modinfo_imgs, secondary = gather_map_preview_candidates(names, lvl_dirs, lvl_infos)
    ordered = primary + modinfo_imgs + secondary

    # Pass 1: Prefer crisp >= 450px wide passing quality checks
    for n in ordered:
        raw = zf.read(n)
        if is_good_game_preview(raw, min_width=450):
            dims = save_resized_jpeg(raw, out_path, max_w=640, quality=78)
            if dims:
                return dims

    # Pass 2: Allow >= 300px wide passing quality checks
    for n in ordered:
        raw = zf.read(n)
        if is_good_game_preview(raw, min_width=300):
            dims = save_resized_jpeg(raw, out_path, max_w=640, quality=78)
            if dims:
                return dims

    # Pass 3: Terrain heightmap relief fallback (e.g. TwinRingByJosh without real screenshot)
    for n in names:
        nl = n.lower()
        if ("height_source" in nl or "heightmap" in nl) and nl.endswith((".png", ".jpg")):
            dims = render_relief_from_heightmap(zf.read(n), out_path)
            if dims:
                return dims

    # Final fallback: any listed entry
    for n in ordered:
        dims = save_resized_jpeg(zf.read(n), out_path, max_w=640, quality=78)
        if dims:
            return dims
    return None

def pick_car_preview(names, veh_dirs):
    for d in veh_dirs:
        for cand_name in ("default.png", "default.jpg"):
            cand = f"vehicles/{d}/{cand_name}".lower()
            for n in names:
                if n.lower() == cand:
                    return n
    for d in veh_dirs:
        prefix = f"vehicles/{d}/".lower()
        for n in names:
            nl = n.lower()
            if nl.startswith(prefix) and nl.endswith((".png", ".jpg", ".jpeg")):
                rel = nl[len(prefix):]
                if "/" not in rel and not any(b in rel for b in BAD_IMG_WORDS):
                    return n
    for n in names:
        nl = n.lower()
        if nl.startswith("mod_info/") and ("/thumbs/" in nl or "/images/" in nl or nl.endswith("icon.jpg")) and nl.endswith((".jpg", ".jpeg", ".png")):
            return n
    return None

def url_filename_lower(url: str) -> str:
    return urllib.parse.unquote(url.split("/")[-1].split("?")[0]).lower()

def is_valid_photo_entry(entry: dict, allow_rear_or_detail: bool = False, is_map: bool = False) -> bool:
    if not entry or not entry.get("url"):
        return False
    url = entry["url"]
    w = int(entry.get("width") or 0)
    h = int(entry.get("height") or 0)
    fn = url_filename_lower(url)
    # Require genuine photographic raster formats (.jpg / .jpeg)
    if not fn.endswith((".jpg", ".jpeg")):
        return False
    if any(tok in fn for tok in NON_PHOTO_URL_TOKENS):
        return False
    if w < 300 or h < 180:
        return False
    ratio = w / float(h)
    if ratio < 0.72 or ratio > 2.4:
        return False
    if not is_map and not allow_rear_or_detail and CAR_DETAIL_RE.search(fn):
        return False
    return True

def http_get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))

def fetch_wiki_pageimages_batch(titles: list[str], cache: dict):
    missing = [t for t in titles if t and t not in cache]
    if not missing:
        return
    for i in range(0, len(missing), 40):
        chunk = missing[i:i + 40]
        joined = "|".join(chunk)
        url = (
            "https://en.wikipedia.org/w/api.php?action=query&format=json"
            "&prop=pageimages&piprop=thumbnail&pithumbsize=800&redirects=1&titles="
            + urllib.parse.quote(joined)
        )
        try:
            data = http_get_json(url)
            q = data.get("query", {})
            norm_map = {n["from"]: n["to"] for n in q.get("normalized", [])}
            redir_map = {r["from"]: r["to"] for r in q.get("redirects", [])}
            pages = q.get("pages", {})
            title_to_info = {}
            for p in pages.values():
                t = p.get("title")
                thumb = p.get("thumbnail") or {}
                src = thumb.get("source")
                if t and src:
                    title_to_info[t] = {
                        "url": src,
                        "width": int(thumb.get("width") or 800),
                        "height": int(thumb.get("height") or 533),
                    }
            for orig in chunk:
                cur = norm_map.get(orig, orig)
                cur = redir_map.get(cur, cur)
                if cur in title_to_info:
                    cache[orig] = title_to_info[cur]
        except Exception as e:
            print("Wiki batch error:", e)
        time.sleep(0.15)

def fetch_commons_candidates(query: str, commons_cache: dict, limit: int = 15) -> list[dict]:
    if query in commons_cache:
        return commons_cache[query]
    url = (
        f"https://commons.wikimedia.org/w/api.php?action=query&format=json"
        f"&generator=search&gsrnamespace=6&gsrlimit={limit}&prop=imageinfo&iiprop=url|size&iiurlwidth=800&gsrsearch="
        + urllib.parse.quote(query)
    )
    results = []
    try:
        data = http_get_json(url)
        pages = list((data.get("query", {}).get("pages", {})).values())
        pages.sort(key=lambda x: x.get("index", 99))
        for p in pages:
            ii = (p.get("imageinfo") or [{}])[0]
            u = ii.get("thumburl") or ii.get("url")
            w = ii.get("thumbwidth") or ii.get("width") or 800
            h = ii.get("thumbheight") or ii.get("height") or 533
            if u:
                results.append({"url": u, "width": int(w), "height": int(h)})
    except Exception as e:
        print(f"Commons search error [{query}]:", e)
    commons_cache[query] = results
    time.sleep(0.12)
    return results

def search_best_photo(query: str, wiki_cache: dict, commons_cache: dict, is_map: bool = False):
    cands = fetch_commons_candidates(query, commons_cache, limit=15)
    for prefer_landscape in (True, False):
        for entry in cands:
            if not is_valid_photo_entry(entry, allow_rear_or_detail=False, is_map=is_map):
                continue
            if prefer_landscape and entry["width"] <= entry["height"]:
                continue
            wiki_cache[query] = entry
            return entry

    # Fallback: Wikipedia search pageimages validated as JPG photo
    wp_url = (
        "https://en.wikipedia.org/w/api.php?action=query&format=json"
        "&generator=search&gsrlimit=5&prop=pageimages&piprop=thumbnail&pithumbsize=800&gsrsearch="
        + urllib.parse.quote(query)
    )
    try:
        data = http_get_json(wp_url)
        pages = list((data.get("query", {}).get("pages", {})).values())
        pages.sort(key=lambda x: x.get("index", 99))
        for p in pages:
            thumb = p.get("thumbnail") or {}
            entry = {
                "url": thumb.get("source") or "",
                "width": int(thumb.get("width") or 800),
                "height": int(thumb.get("height") or 533),
            }
            if is_valid_photo_entry(entry, allow_rear_or_detail=True, is_map=is_map):
                wiki_cache[query] = entry
                return entry
    except Exception:
        pass

    for entry in cands:
        if is_valid_photo_entry(entry, allow_rear_or_detail=True, is_map=is_map):
            wiki_cache[query] = entry
            return entry
    return None

def pick_unique_car_photo(car: dict, wiki_cache: dict, commons_cache: dict, used_urls: set[str]):
    query = car["realCarQuery"]
    primary = wiki_cache.get(query)
    if is_valid_photo_entry(primary, allow_rear_or_detail=False, is_map=False) and primary["url"] not in used_urls:
        used_urls.add(primary["url"])
        return primary

    # Try unused exterior landscape JPGs from Wikimedia Commons for query variations
    search_variants = [query]
    if car["displayName"] and car["displayName"].lower() != query.lower():
        search_variants.append(car["displayName"])
    search_variants.append(f"{query} front")

    fallback_valid = primary if is_valid_photo_entry(primary, allow_rear_or_detail=True, is_map=False) else None

    for sv in search_variants:
        cands = fetch_commons_candidates(sv, commons_cache, limit=18)
        for allow_detail in (False, True):
            for entry in cands:
                if not is_valid_photo_entry(entry, allow_rear_or_detail=allow_detail, is_map=False):
                    continue
                if fallback_valid is None:
                    fallback_valid = entry
                if entry["width"] >= entry["height"] and entry["url"] not in used_urls:
                    used_urls.add(entry["url"])
                    return entry

    # Any orientation unused JPG
    for sv in search_variants:
        for entry in fetch_commons_candidates(sv, commons_cache, limit=18):
            if is_valid_photo_entry(entry, allow_rear_or_detail=True, is_map=False) and entry["url"] not in used_urls:
                used_urls.add(entry["url"])
                return entry

    if fallback_valid:
        return fallback_valid
    return None

def aspect_from_slug(s: str, is_map: bool = False) -> str:
    h = int(hashlib.md5(s.encode("utf-8")).hexdigest()[:4], 16) % 10
    if is_map:
        return "wide" if h % 2 == 0 else "medium"
    if h in (0, 5):
        return "tall"
    if h in (1, 6, 8):
        return "medium"
    if h in (2, 7):
        return "wide"
    return "square"

def main():
    MAPS_THUMB_DIR.mkdir(parents=True, exist_ok=True)
    CARS_THUMB_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    cache = json.loads(CACHE_FILE.read_text(encoding="utf-8")) if CACHE_FILE.exists() else {}
    commons_cache = json.loads(COMMONS_CACHE_FILE.read_text(encoding="utf-8")) if COMMONS_CACHE_FILE.exists() else {}

    zips = [("mods", p) for p in sorted(MODS_ROOT.glob("*.zip"))] + [("repo", p) for p in sorted((MODS_ROOT / "repo").glob("*.zip"))]

    raw_maps = []
    raw_cars = []

    for src, p in zips:
        zl = p.name.lower()
        with zipfile.ZipFile(p, "r") as zf:
            names = zf.namelist()
            lvl_dirs = sorted({
                n.split("/")[1] for n in names
                if n.lower().startswith("levels/") and len(n.split("/")) > 2
                and n.split("/")[1] and n.split("/")[1].lower() not in ("gameplay", "vehicles", "art")
            })

            if lvl_dirs:
                if zl in SKIP_MAP_ZIPS:
                    continue
                lvl_infos = {}
                mod_info = None
                for n in names:
                    nl = n.lower()
                    if nl.startswith("mod_info/") and nl.endswith("/info.json") and nl.count("/") == 2:
                        d = load_lenient_json(zf.read(n))
                        if isinstance(d, dict):
                            mod_info = d
                    if nl.startswith("levels/") and nl.endswith("/info.json") and nl.count("/") == 2:
                        d = load_lenient_json(zf.read(n))
                        if isinstance(d, dict):
                            lvl_infos[n.split("/")[1]] = d

                main_dir = lvl_dirs[0]
                li = lvl_infos.get(main_dir) or (list(lvl_infos.values())[0] if lvl_infos else {})
                mi_title = (mod_info or {}).get("title") or ""
                li_title = li.get("title") or ""
                desc = li.get("description") or (mod_info or {}).get("tag_line") or ""
                if desc.startswith("levels."):
                    desc = ""

                slug = slugify(p.name)
                out_jpg = MAPS_THUMB_DIR / f"{slug}.jpg"
                thumb_dims = pick_best_map_preview(zf, names, lvl_dirs, lvl_infos, out_jpg)
                game_thumb_rel = f"/thumbnails/maps/{slug}.jpg" if thumb_dims else ""
                tw, th = thumb_dims if thumb_dims else (640, 360)

                is_real = zl in REAL_MAPS_MAP
                if is_real:
                    dname, wquery, loc_label = REAL_MAPS_MAP[zl]
                    commons_override = MAP_COMMONS_PHOTO_QUERIES.get(zl)
                else:
                    dname = FICTIONAL_DISPLAY_OVERRIDES.get(zl) or li_title or mi_title or p.stem.replace("_", " ")
                    wquery = ""
                    loc_label = None
                    commons_override = None

                raw_maps.append({
                    "id": slug,
                    "zipName": p.name,
                    "source": src,
                    "internalId": main_dir,
                    "displayName": dname.strip(),
                    "description": desc.strip()[:160],
                    "isRealWorld": is_real,
                    "realLocationName": loc_label,
                    "wikiQuery": wquery,
                    "commonsQuery": commons_override,
                    "gameImageUrl": game_thumb_rel,
                    "gameThumbWidth": tw,
                    "gameThumbHeight": th,
                    "aspectRatio": aspect_from_slug(slug, is_map=True),
                })
                continue

            # Vehicles
            if zl in SKIP_CAR_ZIPS:
                continue
            veh_dirs = sorted({
                n.split("/")[1] for n in names
                if n.lower().startswith("vehicles/") and len(n.split("/")) > 2
                and n.split("/")[1] and not n.split("/")[1].lower().endswith((".txt", ".jbeam", ".png"))
                and n.split("/")[1].lower() not in ("art", "enginesounds")
            })
            custom_vehs = [v for v in veh_dirs if v.lower() not in VANILLA_VEHICLES]
            if not custom_vehs:
                continue

            mod_info_title = None
            veh_infos = {}
            for n in names:
                nl = n.lower()
                if nl.startswith("mod_info/") and nl.endswith("/info.json") and nl.count("/") == 2:
                    d = load_lenient_json(zf.read(n))
                    if isinstance(d, dict):
                        mod_info_title = d.get("title")
                if nl.startswith("vehicles/") and nl.endswith("/info.json") and nl.count("/") == 2:
                    d = load_lenient_json(zf.read(n))
                    if isinstance(d, dict):
                        veh_infos[n.split("/")[1]] = d

            slug = slugify(p.name)
            prev_entry = pick_car_preview(names, custom_vehs)
            car_thumb_rel = ""
            cw, ch = (460, 259)
            if prev_entry:
                out_jpg = CARS_THUMB_DIR / f"{slug}.jpg"
                if out_jpg.exists():
                    with Image.open(out_jpg) as existing_im:
                        cw, ch = existing_im.size
                    car_thumb_rel = f"/thumbnails/cars/{slug}.jpg"
                else:
                    dims = save_resized_jpeg(zf.read(prev_entry), out_jpg, max_w=460, quality=72)
                    if dims:
                        cw, ch = dims
                        car_thumb_rel = f"/thumbnails/cars/{slug}.jpg"

            first_v = custom_vehs[0]
            vinfo = veh_infos.get(first_v) or {}
            brand = (vinfo.get("Brand") or "").strip()
            vname = (vinfo.get("Name") or "").strip()

            if zl in LORE_AND_EXACT_CAR_MAP:
                wquery, dname = LORE_AND_EXACT_CAR_MAP[zl]
                if not brand:
                    brand = dname.split(" ")[0]
            else:
                dname = f"{brand} {vname}".strip() if brand and brand.lower() not in vname.lower() else (vname or mod_info_title or p.stem)
                wquery = dname

            raw_cars.append({
                "id": slug,
                "zipName": p.name,
                "source": src,
                "displayName": dname,
                "brand": brand or dname.split(" ")[0],
                "realCarQuery": wquery,
                "gamePreviewUrl": car_thumb_rel or None,
                "gameThumbWidth": cw,
                "gameThumbHeight": ch,
                "category": "camion" if zl in TRUCK_ZIPS else "auto",
                "aspectRatio": aspect_from_slug(slug, is_map=False),
            })

    # Batch fetch Wikipedia lead images for standard article queries
    wp_titles = sorted(
        {c["realCarQuery"] for c in raw_cars if c["realCarQuery"]}
        | {m["wikiQuery"] for m in raw_maps if m["isRealWorld"] and not m["commonsQuery"] and m["wikiQuery"]}
    )
    print(f"Fetching Wikipedia pageimages for {len(wp_titles)} unique titles...")
    fetch_wiki_pageimages_batch(wp_titles, cache)

    # Curate scenic Commons JPGs for explicit map overrides or invalid Wikipedia map leads
    used_map_urls: set[str] = set()
    final_maps = []
    for m in raw_maps:
        real_entry = None
        if m["isRealWorld"]:
            if m["commonsQuery"]:
                cands = fetch_commons_candidates(m["commonsQuery"], commons_cache, limit=15)
                for prefer_land in (True, False):
                    for cand in cands:
                        if not is_valid_photo_entry(cand, allow_rear_or_detail=True, is_map=True):
                            continue
                        if prefer_land and cand["width"] <= cand["height"]:
                            continue
                        if cand["url"] not in used_map_urls:
                            real_entry = cand
                            break
                    if real_entry:
                        break
                if not real_entry:
                    for cand in cands:
                        if is_valid_photo_entry(cand, allow_rear_or_detail=True, is_map=True):
                            real_entry = cand
                            break
            else:
                cand_wp = cache.get(m["wikiQuery"])
                if is_valid_photo_entry(cand_wp, allow_rear_or_detail=True, is_map=True):
                    real_entry = cand_wp
                else:
                    # Fallback to Commons search for this location
                    real_entry = search_best_photo(m["wikiQuery"], cache, commons_cache, is_map=True)

        real_url = real_entry["url"] if real_entry else None
        if real_url:
            used_map_urls.add(real_url)

        is_real_ok = bool(m["isRealWorld"] and real_url)
        # Split real-world cards use wide 16:9 so both halves stay balanced;
        # Fictional cards use the exact natural pixel ratio of the game preview.
        aw, ah = (16, 9) if is_real_ok else (m["gameThumbWidth"], m["gameThumbHeight"])

        final_maps.append({
            "id": m["id"],
            "zipName": m["zipName"],
            "source": m["source"],
            "internalId": m["internalId"],
            "displayName": m["displayName"],
            "description": m["description"],
            "isRealWorld": is_real_ok,
            "realLocationName": m["realLocationName"],
            "realImageUrl": real_url,
            "gameImageUrl": m["gameImageUrl"],
            "aspectRatio": "wide" if is_real_ok else m["aspectRatio"],
            "aspectWidth": aw,
            "aspectHeight": ah,
        })

    # De-duplicate & validate car photos with exact dimensions
    used_car_urls: set[str] = set()
    final_cars = []
    for c in raw_cars:
        photo = pick_unique_car_photo(c, cache, commons_cache, used_car_urls)
        if photo:
            img_url = photo["url"]
            aw, ah = photo["width"], photo["height"]
        else:
            img_url = c["gamePreviewUrl"] or ""
            aw, ah = c["gameThumbWidth"], c["gameThumbHeight"]

        final_cars.append({
            "id": c["id"],
            "zipName": c["zipName"],
            "source": c["source"],
            "displayName": c["displayName"],
            "brand": c["brand"],
            "realCarQuery": c["realCarQuery"],
            "realImageUrl": img_url,
            "gamePreviewUrl": c["gamePreviewUrl"],
            "category": c["category"],
            "aspectRatio": c["aspectRatio"],
            "aspectWidth": aw,
            "aspectHeight": ah,
        })

    CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
    COMMONS_CACHE_FILE.write_text(json.dumps(commons_cache, indent=2, ensure_ascii=False), encoding="utf-8")

    catalog = {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stats": {
            "totalCars": len(final_cars),
            "totalMaps": len(final_maps),
            "realWorldMaps": sum(1 for m in final_maps if m["isRealWorld"]),
            "fictionalMaps": sum(1 for m in final_maps if not m["isRealWorld"]),
        },
        "cars": final_cars,
        "maps": final_maps,
    }
    OUT_JSON.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Catalog built:", catalog["stats"])

if __name__ == "__main__":
    main()
