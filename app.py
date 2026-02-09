#!/usr/bin/env python3
"""
AHP-BOCR Validation Microservice v2.0
Uses AhpAnpLib directly (Creative Decisions Foundation).

Reference:
  MU, E. Creative Decisions Foundation Announces the Release of AHP/ANP
  Python Library. International Journal of the Analytic Hierarchy Process,
  v. 15, n. 2, 2023. DOI: 10.13033/ijahp.v15i2.1163

Library:
  AhpAnpLib — https://pypi.org/project/AhpAnpLib/
  Creative Decisions Foundation — https://creativedecisions.net
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import traceback

# AhpAnpLib — Creative Decisions Foundation
from AhpAnpLib.calcs_AHPLib import (
    priorityVector,
    calcInconsistency,
    RI
)

app = Flask(__name__)
CORS(app)


# ==============================================================
# HEALTH CHECK
# ==============================================================

@app.route('/', methods=['GET'])
def health():
    try:
        test_matrix = np.array([[1, 2], [0.5, 1]])
        pv = priorityVector(test_matrix)
        lib_ok = bool(len(pv) == 2 and abs(sum(pv) - 1.0) < 0.001)
    except Exception:
        lib_ok = False

    return jsonify({
        'status': 'ok',
        'service': 'AHP-BOCR Validator',
        'version': '2.0.0',
        'library': 'AhpAnpLib (Creative Decisions Foundation)',
        'library_reference': 'Mu, E. (2023). IJAHP, v.15, n.2. DOI: 10.13033/ijahp.v15i2.1163',
        'ahpanplib_available': lib_ok
    })


# ==============================================================
# VALIDATE SINGLE MATRIX
# ==============================================================

@app.route('/validate', methods=['POST'])
def validate():
    try:
        data = request.json
        matrix = np.array(data['matrix'], dtype=float)
        items = data.get('items', [f'Item_{i}' for i in range(len(matrix))])
        your_weights = data.get('your_weights', [])
        your_cr = data.get('your_cr', None)

        n = len(matrix)

        # AhpAnpLib calculations
        sdk_weights = priorityVector(matrix)
        sdk_cr = float(calcInconsistency(matrix))
        sdk_ri = float(RI(n)) if n <= 15 else None

        # lambda_max
        weighted_sum = matrix @ sdk_weights
        sdk_lambda_max = float(np.mean(weighted_sum / sdk_weights))

        # CI
        sdk_ci = (sdk_lambda_max - n) / (n - 1) if n > 1 else 0

        result = {
            'sdk': {
                'library': 'AhpAnpLib',
                'version': '2.6.0',
                'publisher': 'Creative Decisions Foundation',
                'reference': 'Mu (2023), IJAHP v.15 n.2',
                'weights': {items[i]: round(float(sdk_weights[i]), 6) for i in range(n)},
                'weights_array': [round(float(w), 6) for w in sdk_weights],
                'cr': round(sdk_cr, 6),
                'lambda_max': round(sdk_lambda_max, 6),
                'ci': round(sdk_ci, 6),
                'ri': sdk_ri,
                'n': n
            },
            'valid': True,
            'details': []
        }

        if your_weights and len(your_weights) == n:
            your_w = np.array(your_weights, dtype=float)
            diff_weights = np.abs(sdk_weights - your_w)
            max_diff = float(np.max(diff_weights))
            cr_diff = abs(sdk_cr - float(your_cr)) if your_cr is not None else 0

            result['your_system'] = {
                'weights': {items[i]: round(float(your_w[i]), 6) for i in range(n)},
                'weights_array': [round(float(w), 6) for w in your_w],
                'cr': round(float(your_cr), 6) if your_cr is not None else None
            }

            result['comparison'] = {
                'weight_differences': {items[i]: round(float(diff_weights[i]), 6) for i in range(n)},
                'max_weight_diff': round(max_diff, 6),
                'max_weight_diff_pct': round(max_diff * 100, 4),
                'cr_diff': round(cr_diff, 6),
                'weights_match': bool(max_diff < 0.01),
                'cr_match': bool(cr_diff < 0.01)
            }

            result['valid'] = bool(max_diff < 0.01)
            if max_diff < 0.001:
                result['details'].append('Eigenvector: diferenca < 0.1% — EXCELENTE')
            elif max_diff < 0.01:
                result['details'].append('Eigenvector: diferenca < 1% — VALIDO')
            else:
                result['details'].append(f'Eigenvector: diferenca max {max_diff*100:.2f}% — VERIFICAR')

            if your_cr is not None:
                if cr_diff < 0.001:
                    result['details'].append('CR: diferenca < 0.1% — EXCELENTE')
                elif cr_diff < 0.01:
                    result['details'].append('CR: diferenca < 1% — VALIDO')
                else:
                    result['details'].append(f'CR: diferenca {cr_diff*100:.2f}% — VERIFICAR')

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc(),
            'valid': False
        }), 400


# ==============================================================
# VALIDATE FULL PROJECT
# ==============================================================

@app.route('/validate-project', methods=['POST'])
def validate_project():
    try:
        data = request.json
        matrices = data.get('matrices', {})
        results = {}
        all_valid = True
        summary = {
            'total_matrices': 0,
            'valid_matrices': 0,
            'max_weight_diff': 0,
            'max_cr_diff': 0,
            'issues': []
        }

        for name, matrix_data in matrices.items():
            matrix = np.array(matrix_data['matrix'], dtype=float)
            items = matrix_data.get('items', [])
            your_weights = matrix_data.get('your_weights', [])
            your_cr = matrix_data.get('your_cr', None)

            n = len(matrix)
            sdk_weights = priorityVector(matrix)
            sdk_cr = float(calcInconsistency(matrix))

            weighted_sum = matrix @ sdk_weights
            sdk_lmax = float(np.mean(weighted_sum / sdk_weights))

            summary['total_matrices'] += 1

            mat_result = {
                'sdk_weights': [round(float(w), 6) for w in sdk_weights],
                'sdk_cr': round(sdk_cr, 6),
                'sdk_lambda_max': round(sdk_lmax, 6),
                'items': items,
                'n': n,
                'valid': True
            }

            if your_weights and len(your_weights) == n:
                your_w = np.array(your_weights, dtype=float)
                diff = np.abs(sdk_weights - your_w)
                max_diff = float(np.max(diff))
                cr_diff = abs(sdk_cr - float(your_cr)) if your_cr is not None else 0

                mat_result['your_weights'] = [round(float(w), 6) for w in your_w]
                mat_result['your_cr'] = round(float(your_cr), 6) if your_cr is not None else None
                mat_result['max_weight_diff'] = round(max_diff, 6)
                mat_result['cr_diff'] = round(cr_diff, 6)
                mat_result['valid'] = bool(max_diff < 0.01)

                summary['max_weight_diff'] = max(summary['max_weight_diff'], max_diff)
                summary['max_cr_diff'] = max(summary['max_cr_diff'], cr_diff)

                if max_diff < 0.01:
                    summary['valid_matrices'] += 1
                else:
                    all_valid = False
                    summary['issues'].append(f'{name}: diff={max_diff*100:.2f}%')
            else:
                mat_result['sdk_only'] = True
                summary['valid_matrices'] += 1

            results[name] = mat_result

        return jsonify({
            'results': results,
            'summary': {
                'total_matrices': summary['total_matrices'],
                'valid_matrices': summary['valid_matrices'],
                'max_weight_diff': round(summary['max_weight_diff'], 6),
                'max_cr_diff': round(summary['max_cr_diff'], 6),
                'issues': summary['issues']
            },
            'all_valid': bool(all_valid),
            'library': 'AhpAnpLib (Creative Decisions Foundation)',
            'citation': 'Mu, E. (2023). Creative Decisions Foundation Announces the Release of AHP/ANP Python Library. IJAHP, v.15, n.2. DOI: 10.13033/ijahp.v15i2.1163'
        })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 400


# ==============================================================
# STANDALONE CALCULATION
# ==============================================================

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.json
        matrix = np.array(data['matrix'], dtype=float)
        items = data.get('items', [f'Item_{i}' for i in range(len(matrix))])
        n = len(matrix)

        weights = priorityVector(matrix)
        cr = float(calcInconsistency(matrix))
        ri = float(RI(n)) if n <= 15 else None

        weighted_sum = matrix @ weights
        lmax = float(np.mean(weighted_sum / weights))
        ci = (lmax - n) / (n - 1) if n > 1 else 0

        return jsonify({
            'weights': {items[i]: round(float(weights[i]), 6) for i in range(n)},
            'weights_array': [round(float(w), 6) for w in weights],
            'cr': round(cr, 6),
            'ci': round(ci, 6),
            'lambda_max': round(lmax, 6),
            'ri': ri,
            'n': n,
            'consistent': bool(cr <= 0.10),
            'library': 'AhpAnpLib (Creative Decisions Foundation)'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
