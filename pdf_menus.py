# -*- coding: utf-8 -*-
"""
Fiche PDF et conversions — REPRIS TEL QUEL de ton application « gestion-menus ».

Pourquoi tel quel : ta fiche PDF fonctionne bien et tu en es content. Je ne la
réécris pas, je la garde à l'identique — c'est la même mise en page, la même
liste de courses, le même récapitulatif de la semaine.

Seule modification : les fonctions de calcul de quantité ont été branchées sur
le moteur de la version 2.0 (elles donnent les mêmes résultats).
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
import base64
import re

import streamlit as st
import streamlit.components.v1 as components
from fpdf import FPDF

# ---------------------------------------------------------------------------
#  CONSTANTES — reprises de ton application (mêmes libellés, mêmes rayons)
# ---------------------------------------------------------------------------
UNITES = ["g", "kg", "ml", "cl", "l", "unité", "pièce", "tranche", "gousse",
          "sachet", "boîte", "barquette", "c. à soupe", "c. à café", "pincée"]

RAYONS = ["Fruits & Légumes", "Boucherie & Poissonnerie", "Frais & Produits Laitiers",
          "Épicerie Salée", "Épicerie Sucrée", "Boissons", "Surgelés", "Autre"]

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
REPAS = ["Midi", "Soir"]

JOURS_FR = {"Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi",
            "Thursday": "Jeudi", "Friday": "Vendredi", "Saturday": "Samedi",
            "Sunday": "Dimanche"}

REPAS_LABELS = {"Midi": "Déjeuner", "Soir": "Dîner"}


def clean_pdf_str(text: Any) -> str:
    if not text:
        return ""
    
    replacements = {
        '✂️': '-', '🍽️': '', '📖': '', '📝': '', '🛒': '', '•': '-',
        'é': 'e', 'è': 'e', 'ê': 'e', 'à': 'a', 'ç': 'c', 'ù': 'u',
        'ô': 'o', 'î': 'i', 'ï': 'i', 'É': 'E', 'È': 'E', 'Ê': 'E',
        'À': 'A', 'Ç': 'C', 'Ù': 'U', 'Ô': 'O', 'Î': 'I', 'Ï': 'I',
        '€': 'EUR', '"': '"', '"': '"', ''': "'", ''': "'",
    }
    
    result = str(text)
    for old, new in replacements.items():
        result = result.replace(old, new)
    
    return result.encode('latin-1', 'replace').decode('latin-1')

def format_quantity(qty: float) -> str:
    if isinstance(qty, float) and qty.is_integer():
        return str(int(qty))
    return f"{qty:.2f}".rstrip('0').rstrip('.')

def format_servings(servings: float) -> str:
    if servings == int(servings):
        return str(int(servings))
    return str(servings)

def format_liste_quantity(qty: float, unit: str) -> tuple:
    if unit in ['g', 'gramme', 'grammes'] and qty >= 1000:
        return qty / 1000, 'kg'
    elif unit in ['ml', 'millilitre'] and qty >= 1000:
        return qty / 1000, 'l'
    else:
        return qty, unit

def instructions_to_text(instructions_list: List[str]) -> str:
    if not instructions_list:
        return ""
    return "\n".join([f"{i+1}. {instr}" for i, instr in enumerate(instructions_list) if instr.strip()])

def text_to_instructions(text: str) -> List[str]:
    if not text:
        return [""]
    
    lines = text.split('\n')
    instructions = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = re.match(r'^\d+\.\s*', line)
        if match:
            instructions.append(line[match.end():])
        else:
            instructions.append(line)
    
    return instructions if instructions else [""]

def sort_list_by_name(items: List[Dict]) -> List[Dict]:
    return sorted(items, key=lambda x: x.get('name', '').lower())

def get_display_name(recipe: Dict) -> str:
    name = recipe.get('name', '')
    if name.startswith('[Ing] '):
        return name[6:]
    if name.startswith('[Txt] '):
        return name[6:]
    return name

def open_pdf_button(pdf_bytes: bytes):
    b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    
    html_component = f"""
    <button id="open-pdf-btn" style="
        width: 100%;
        padding: 12px 20px;
        color: white;
        background-color: #4CAF50;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        font-size: 16px;
        cursor: pointer;
        margin-bottom: 10px;">
        📄 Ouvrir le PDF dans un nouvel onglet
    </button>
    <script>
    document.getElementById("open-pdf-btn").addEventListener("click", function() {{
        const b64Data = "{b64_pdf}";
        const byteCharacters = atob(b64Data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {{
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }}
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], {{ type: "application/pdf" }});
        const url = URL.createObjectURL(blob);
        window.open(url, "_blank");
        
        setTimeout(() => {{
            URL.revokeObjectURL(url);
        }}, 60000);
    }});
    </script>
    """
    
    components.html(html_component, height=60)

def convert_to_unit(quantity: float, unit_source: str, unit_cible: str, poids_piece_g: float = None) -> float:
    unit_source = unit_source.lower().strip() if unit_source else ""
    unit_cible = unit_cible.lower().strip() if unit_cible else ""
    
    if unit_source in ['g', 'gramme', 'grammes']:
        qty_kg = quantity / 1000
    elif unit_source in ['kg', 'kilo', 'kilos']:
        qty_kg = quantity
    elif unit_source in ['ml', 'millilitre']:
        qty_kg = quantity / 1000
    elif unit_source in ['cl', 'centilitre']:
        qty_kg = quantity / 100
    elif unit_source in ['l', 'litre']:
        qty_kg = quantity
    elif unit_source in ['c. à soupe', 'cuillère à soupe']:
        qty_kg = quantity * 0.015
    elif unit_source in ['c. à café', 'cuillère à café']:
        qty_kg = quantity * 0.005
    elif unit_source in ['unité', 'pièce', 'tranche', 'gousse', 'sachet', 'boîte', 'barquette']:
        if poids_piece_g is not None and poids_piece_g > 0:
            qty_kg = (quantity * poids_piece_g) / 1000
        else:
            qty_kg = quantity
    else:
        qty_kg = quantity
    
    if unit_cible in ['g', 'gramme', 'grammes']:
        return qty_kg * 1000
    elif unit_cible in ['kg', 'kilo', 'kilos']:
        return qty_kg
    elif unit_cible in ['ml', 'millilitre']:
        return qty_kg * 1000
    elif unit_cible in ['cl', 'centilitre']:
        return qty_kg * 100
    elif unit_cible in ['l', 'litre']:
        return qty_kg
    elif unit_cible in ['unité', 'pièce', 'tranche', 'gousse', 'sachet', 'boîte', 'barquette']:
        if poids_piece_g is not None and poids_piece_g > 0:
            return qty_kg * 1000 / poids_piece_g
        else:
            return qty_kg
    else:
        return qty_kg

# ------------------------------

def generate_pdf(planned_meals: List[Dict], aggregated_items: Dict,
                 recurrent_items: List[Dict], recipes_dict: Dict, 
                 ingredients_dict: Dict = None,
                 start_date: date = None) -> bytes:
    try:
        pdf = FPDF(format='A4', unit='mm')
        pdf.set_auto_page_break(auto=False)
        pdf.add_page()
        
        page_width = 210
        page_height = 297
        margin = 10
        left_width = 115
        right_width = 68
        gap = 5
        day_block_width = 15
        
        green_bg = (200, 230, 200)
        orange_bg = (255, 220, 180)
        gray_bg = (240, 240, 240)
        midi_bg = (255, 250, 240)
        soir_bg = (240, 245, 255)
        day_bg = (245, 245, 220)
        
        title_font_size = 28
        period_font_size = 20
        day_font_size = 13
        meal_font_size = 11
        courses_font_size = 10
        courses_line_height = 4.5
        
        left_x = margin
        right_x = margin + left_width + gap
        
        pdf.set_draw_color(150, 150, 150)
        pdf.set_dash_pattern(dash=1, gap=2)
        pdf.line(right_x - gap/2, margin, right_x - gap/2, page_height - margin)
        pdf.set_dash_pattern()
        
        if start_date:
            week_days = []
            for i in range(7):
                current_date = start_date + timedelta(days=i)
                english_day = current_date.strftime('%A')
                french_day = JOURS_FR.get(english_day, english_day)
                week_days.append({'day_name': french_day, 'date': current_date})
        else:
            week_days = [{'day_name': d, 'date': None} for d in JOURS]
        
        schedule = {}
        for day_info in week_days:
            day_name = day_info['day_name']
            day_date = day_info['date']
            schedule[day_name] = {"Midi": [], "Soir": []}
            
            for pm in planned_meals:
                if day_date and pm.get('date_menu'):
                    if pm.get('date_menu') != day_date.isoformat():
                        continue
                elif pm.get('day') != day_name:
                    continue
                
                rec = recipes_dict.get(pm.get('recipe_id'))
                if rec:
                    rec_name = get_display_name(rec)
                    is_ingredient = rec['name'].startswith('[Ing] ')
                    ingredient_qty = pm.get('ingredient_qty')
                    
                    if is_ingredient and ingredient_qty:
                        ing_unit = None
                        if ingredients_dict:
                            for ing in ingredients_dict.values():
                                if ing['name'] == rec_name:
                                    ing_unit = ing['unit']
                                    break
                        if ing_unit:
                            rec_name = f"{rec_name} ({format_quantity(ingredient_qty)} {ing_unit})"
                        else:
                            rec_name = f"{rec_name} ({format_quantity(ingredient_qty)})"
                else:
                    rec_name = 'Inconnu'
                
                meal_type = pm.get('meal_type')
                if meal_type in schedule[day_name]:
                    schedule[day_name][meal_type].append({
                        'name': rec_name,
                        'servings': pm.get('servings', 1),
                        'has_recipe': pm.get('recipe_id') is not None
                    })
        
        pdf.set_font('Helvetica', 'B', title_font_size)
        pdf.set_xy(left_x, margin)
        pdf.cell(left_width, 12, clean_pdf_str('Menus de la semaine'), align='C')
        
        if start_date:
            end_date = start_date + timedelta(days=6)
            pdf.set_font('Helvetica', '', period_font_size)
            pdf.set_xy(left_x, margin + 12)
            pdf.cell(left_width, 8, clean_pdf_str(f'Du {start_date.strftime("%d/%m/%Y")} au {end_date.strftime("%d/%m/%Y")}'), align='C')
        
        y_start = margin + 22
        
        planning_title_height = 7
        pdf.set_fill_color(*green_bg)
        pdf.set_xy(left_x, y_start)
        pdf.set_font('Helvetica', 'B', 13)
        pdf.cell(left_width, planning_title_height, 'Planning des Repas', ln=True, fill=True, align='C')
        
        planning_right_edge = left_x + left_width
        content_y_start = y_start + planning_title_height + 2
        
        total_available = page_height - margin - content_y_start
        day_gap = 1.5
        days_available = total_available - (len(week_days) - 1) * day_gap
        day_height = days_available / len(week_days)
        
        pdf.set_font('Helvetica', 'B', day_font_size)
        dimanche_width = pdf.get_string_width('Dimanche')
        min_height = dimanche_width + 6
        
        if day_height < min_height:
            day_height = min_height
            total_needed = day_height * len(week_days) + (len(week_days) - 1) * day_gap
            if total_needed > total_available:
                day_height = (total_available - (len(week_days) - 1) * day_gap) / len(week_days)
        
        inner_height = day_height - 1
        title_space = 4
        food_space = max(inner_height - title_space, 2)
        
        max_lines_per_day = 0
        for day_info in week_days:
            day_name = day_info['day_name']
            midi_count = max(len(schedule[day_name]['Midi']), 1)
            soir_count = max(len(schedule[day_name]['Soir']), 1)
            max_lines_per_day = max(max_lines_per_day, midi_count + soir_count)
        
        if max_lines_per_day > 0:
            meal_line_height = food_space / max_lines_per_day
            meal_line_height = max(2.5, min(meal_line_height, 5))
        else:
            meal_line_height = 4
        
        meal_spacing = 0.5
        y = content_y_start
        
        for i, day_info in enumerate(week_days):
            day_name = day_info['day_name']
            midi_items = schedule[day_name]['Midi']
            soir_items = schedule[day_name]['Soir']
            
            content_x = left_x + day_block_width + 2
            content_width = planning_right_edge - content_x
            
            total_inner_height = day_height - 0.5
            interline = 1
            remaining_height = total_inner_height - interline
            
            midi_lines = max(len(midi_items), 1)
            soir_lines = max(len(soir_items), 1)
            total_lines = midi_lines + soir_lines
            
            if total_lines > 0:
                midi_height = (remaining_height * midi_lines / total_lines)
                soir_height = remaining_height - midi_height
            else:
                midi_height = remaining_height / 2
                soir_height = remaining_height / 2
            
            pdf.set_fill_color(*day_bg)
            pdf.rect(left_x, y, day_block_width, total_inner_height, 'F')
            pdf.set_draw_color(200, 200, 200)
            pdf.rect(left_x, y, day_block_width, total_inner_height, 'D')
            
            pdf.set_font('Helvetica', 'B', day_font_size)
            text_margin = 2
            with pdf.rotation(90, left_x + day_block_width/2, y + total_inner_height/2):
                text_width = total_inner_height - (text_margin * 2)
                text_height = day_block_width - 2
                pdf.set_xy(left_x + day_block_width/2 - text_width/2, y + total_inner_height/2 - text_height/2)
                pdf.cell(text_width, text_height, clean_pdf_str(day_name), align='C')
            
            pdf.set_fill_color(*midi_bg)
            pdf.rect(content_x, y, content_width, midi_height, 'F')
            pdf.set_draw_color(220, 220, 220)
            pdf.rect(content_x, y, content_width, midi_height, 'D')
            
            has_midi_content = any(item['has_recipe'] for item in midi_items)
            
            if has_midi_content:
                midi_servings = max([item['servings'] for item in midi_items if item['has_recipe']], default=1)
                midi_servings_str = format_servings(midi_servings)
                midi_label = f'Déjeuner ({midi_servings_str}) :'
            else:
                midi_label = 'Déjeuner :'
            
            pdf.set_xy(content_x + 3, y + 0.5)
            pdf.set_font('Helvetica', 'B', meal_font_size)
            pdf.cell(38, meal_line_height, clean_pdf_str(midi_label), border=0)
            
            if midi_items:
                pdf.set_font('Helvetica', '', meal_font_size)
                pdf.set_xy(content_x + 41, y + 0.5)
                pdf.cell(content_width - 46, meal_line_height, clean_pdf_str(midi_items[0]['name'])[:45], border=0, ln=True)
                y_content = y + 0.5 + meal_line_height + meal_spacing
                
                for item in midi_items[1:]:
                    if y_content + meal_line_height > y + midi_height - 0.5:
                        break
                    pdf.set_xy(content_x + 41, y_content)
                    pdf.cell(content_width - 46, meal_line_height, clean_pdf_str(item['name'])[:45], border=0, ln=True)
                    y_content += meal_line_height + meal_spacing
            else:
                pdf.set_font('Helvetica', 'I', meal_font_size)
                pdf.set_xy(content_x + 41, y + 0.5)
                pdf.cell(content_width - 46, meal_line_height, '-', border=0, ln=True)
            
            y_diner = y + midi_height + interline
            
            pdf.set_fill_color(*soir_bg)
            pdf.rect(content_x, y_diner, content_width, soir_height, 'F')
            pdf.set_draw_color(220, 220, 220)
            pdf.rect(content_x, y_diner, content_width, soir_height, 'D')
            
            has_soir_content = any(item['has_recipe'] for item in soir_items)
            
            if has_soir_content:
                soir_servings = max([item['servings'] for item in soir_items if item['has_recipe']], default=1)
                soir_servings_str = format_servings(soir_servings)
                soir_label = f'Dîner ({soir_servings_str}) :'
            else:
                soir_label = 'Dîner :'
            
            pdf.set_xy(content_x + 3, y_diner + 0.5)
            pdf.set_font('Helvetica', 'B', meal_font_size)
            pdf.cell(38, meal_line_height, clean_pdf_str(soir_label), border=0)
            
            if soir_items:
                pdf.set_font('Helvetica', '', meal_font_size)
                pdf.set_xy(content_x + 41, y_diner + 0.5)
                pdf.cell(content_width - 46, meal_line_height, clean_pdf_str(soir_items[0]['name'])[:45], border=0, ln=True)
                y_content = y_diner + 0.5 + meal_line_height + meal_spacing
                
                for item in soir_items[1:]:
                    if y_content + meal_line_height > y_diner + soir_height - 0.5:
                        break
                    pdf.set_xy(content_x + 41, y_content)
                    pdf.cell(content_width - 46, meal_line_height, clean_pdf_str(item['name'])[:45], border=0, ln=True)
                    y_content += meal_line_height + meal_spacing
            else:
                pdf.set_font('Helvetica', 'I', meal_font_size)
                pdf.set_xy(content_x + 41, y_diner + 0.5)
                pdf.cell(content_width - 46, meal_line_height, '-', border=0, ln=True)
            
            y += day_height + day_gap
        
        y_right = margin
        
        pdf.set_fill_color(*orange_bg)
        pdf.set_xy(right_x, y_right)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(right_width, 8, 'Liste de Courses', ln=True, fill=True, align='C')
        
        y_right += 10
        
        by_cat = defaultdict(list)
        for item in aggregated_items.values():
            by_cat[item.get('category', 'Autre')].append(item)
        
        if not by_cat:
            pdf.set_xy(right_x + 3, y_right)
            pdf.set_font('Helvetica', 'I', courses_font_size)
            pdf.cell(right_width - 6, 5, 'Aucun article', ln=True)
            y_right += 5
        else:
            for cat in RAYONS:
                if cat in by_cat:
                    pdf.set_fill_color(255, 240, 220)
                    pdf.set_xy(right_x, y_right)
                    pdf.set_font('Helvetica', 'B', courses_font_size)
                    pdf.cell(right_width, courses_line_height + 1, clean_pdf_str(cat), ln=True, fill=True)
                    y_right += courses_line_height + 1
                    
                    pdf.set_font('Helvetica', '', courses_font_size)
                    for it in by_cat[cat]:
                        qty = it['qty']
                        unit = it.get('unit', '')
                        
                        qty_display, unit_display = format_liste_quantity(qty, unit)
                        qty_str = format_quantity(qty_display)
                        
                        checkbox_size = 2.5
                        pdf.set_draw_color(100, 100, 100)
                        pdf.rect(right_x + 3, y_right + 1, checkbox_size, checkbox_size, 'D')
                        
                        line = f"{it['name']} : {qty_str} {unit_display}"
                        pdf.set_xy(right_x + 7, y_right)
                        pdf.cell(right_width - 10, courses_line_height, clean_pdf_str(line), ln=True)
                        y_right += courses_line_height
                    
                    y_right += 1
        
        if recurrent_items:
            y_right += 3
            
            pdf.set_fill_color(*gray_bg)
            pdf.set_xy(right_x, y_right)
            pdf.set_font('Helvetica', 'B', courses_font_size)
            pdf.cell(right_width, 7, 'Produits récurrents', ln=True, fill=True, align='C')
            y_right += 9
            
            col_width = (right_width - 10) / 2
            pdf.set_font('Helvetica', '', courses_font_size)
            
            for idx, rec in enumerate(recurrent_items):
                if y_right > page_height - margin - 2:
                    break
                
                if idx % 2 == 0:
                    x_pos = right_x + 3
                else:
                    x_pos = right_x + 5 + col_width
                
                checkbox_size = 2.5
                pdf.set_draw_color(100, 100, 100)
                pdf.rect(x_pos, y_right + 1, checkbox_size, checkbox_size, 'D')
                
                pdf.set_xy(x_pos + 4, y_right)
                pdf.cell(col_width - 4, courses_line_height, clean_pdf_str(rec['name']), ln=False)
                
                if idx % 2 == 1:
                    y_right += courses_line_height
            
            if len(recurrent_items) % 2 != 0:
                y_right += courses_line_height

        return bytes(pdf.output())
    
    except Exception as e:
        st.error(f"Erreur lors de la génération du PDF : {e}")
        return b""

# ------------------------------
# INTERFACE PRINCIPALE
# ------------------------------

def construire_agregat(week_meals, recipes_dict, ingredients_dict, recipe_ings):
    """Liste de courses de la semaine — meme logique que ton application.

    Renvoie (aggregated, recurrent) au format attendu par generate_pdf().
    """
    aggregated = {}
    for pm in week_meals:
        rec = recipes_dict.get(pm.get("recipe_id"))
        if not rec:
            continue
        nom = rec.get("name") or ""
        if nom.startswith("[Ing] "):
            ing_name = get_display_name(rec)
            ing = next((i for i in ingredients_dict.values() if i.get("name") == ing_name), None)
            if ing and not ing.get("exclude_from_list"):
                unite_liste = ing.get("unite_liste_courses") or ing.get("unit")
                qty_source = pm.get("ingredient_qty") or pm.get("servings") or 1
                qty = convert_to_unit(qty_source, ing.get("unit"), unite_liste, ing.get("poids_piece_g"))
                if ing["id"] not in aggregated:
                    aggregated[ing["id"]] = {"name": ing["name"], "qty": 0,
                                             "unit": unite_liste,
                                             "category": ing.get("category", "Autre")}
                aggregated[ing["id"]]["qty"] += qty or 0
        elif not nom.startswith("[Txt] "):
            ratio = (pm.get("servings") or 1) / (rec.get("base_servings") or 1)
            for ri in recipe_ings:
                if ri.get("recipe_id") != pm.get("recipe_id"):
                    continue
                ing = ingredients_dict.get(ri.get("ingredient_id"))
                if not ing or ing.get("exclude_from_list"):
                    continue
                ri_unit = ri.get("unit") or ing.get("unit")
                unite_liste = ing.get("unite_liste_courses") or ing.get("unit")
                qty = convert_to_unit((ri.get("quantity") or 0) * ratio, ri_unit, unite_liste,
                                      ing.get("poids_piece_g"))
                if ing["id"] not in aggregated:
                    aggregated[ing["id"]] = {"name": ing["name"], "qty": 0,
                                             "unit": unite_liste,
                                             "category": ing.get("category", "Autre")}
                aggregated[ing["id"]]["qty"] += qty or 0
    recurrent = [i for i in ingredients_dict.values() if i.get("is_recurrent")]
    return aggregated, recurrent
