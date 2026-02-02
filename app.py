# AHP Validator Microservice
# Flask API para validação de cálculos AHP usando pyAHP
# Deploy: Railway / Render / Heroku

from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np

# Tentar importar ahpy, senão usar implementação própria
try:
    from ahpy import Compare
    AHPY_AVAILABLE = True
except ImportError:
    AHPY_AVAILABLE = False

app = Flask(__name__)
CORS(app)  # Permitir chamadas do frontend

# ============================================================
# IMPLEMENTAÇÃO DE REFERÊNCIA (caso ahpy não esteja disponível)
# Baseada em Saaty (1980) - método da média geométrica
# ============================================================

# Random Index (RI) - Saaty (1980), Tabela 3.1
RANDOM_INDEX = {
    1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12,
    6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49,
    11: 1.52, 12: 1.54, 13: 1.56, 14: 1.58, 15: 1.59
}

def geometric_mean_method(matrix):
    """
    Calcula eigenvector usando método da média geométrica (Saaty, 1980)
    Este é o método mais comum e recomendado para AHP
    """
    n = len(matrix)
    matrix = np.array(matrix, dtype=float)
    
    # Média geométrica de cada linha
    row_products = np.prod(matrix, axis=1)
    geometric_means = np.power(row_products, 1/n)
    
    # Normalizar
    weights = geometric_means / np.sum(geometric_means)
    
    return weights

def power_method(matrix, max_iter=100, tolerance=1e-6):
    """
    Calcula eigenvector usando método das potências (alternativo)
    Mais preciso para matrizes maiores
    """
    n = len(matrix)
    matrix = np.array(matrix, dtype=float)
    
    # Vetor inicial
    v = np.ones(n) / n
    
    for _ in range(max_iter):
        v_new = np.dot(matrix, v)
        v_new = v_new / np.sum(v_new)
        
        if np.max(np.abs(v_new - v)) < tolerance:
            break
        v = v_new
    
    return v_new

def calculate_consistency(matrix, weights):
    """
    Calcula CR (Consistency Ratio) conforme Saaty (1980)
    CR = CI / RI, onde CI = (λmax - n) / (n - 1)
    """
    n = len(matrix)
    matrix = np.array(matrix, dtype=float)
    weights = np.array(weights)
    
    # Calcular λmax
    weighted_sum = np.dot(matrix, weights)
    lambda_values = weighted_sum / weights
    lambda_max = np.mean(lambda_values)
    
    # Calcular CI
    if n <= 2:
        ci = 0
        cr = 0
    else:
        ci = (lambda_max - n) / (n - 1)
        ri = RANDOM_INDEX.get(n, 1.49)
        cr = ci / ri if ri > 0 else 0
    
    return {
        'lambda_max': float(lambda_max),
        'ci': float(ci),
        'cr': float(cr)
    }

def validate_with_reference(matrix, items):
    """
    Validação usando implementação de referência
    """
    # Método 1: Média geométrica (principal)
    weights_gm = geometric_mean_method(matrix)
    
    # Método 2: Potências (verificação)
    weights_pm = power_method(matrix)
    
    # Consistência
    consistency = calculate_consistency(matrix, weights_gm)
    
    # Verificar convergência entre métodos
    method_diff = np.max(np.abs(weights_gm - weights_pm))
    
    return {
        'weights': weights_gm.tolist(),
        'weights_power_method': weights_pm.tolist(),
        'lambda_max': consistency['lambda_max'],
        'ci': consistency['ci'],
        'cr': consistency['cr'],
        'method_convergence': float(method_diff),
        'methods_agree': method_diff < 0.01
    }

def validate_with_ahpy(matrix, items):
    """
    Validação usando biblioteca ahpy (se disponível)
    """
    n = len(items)
    
    # Converter matriz para formato ahpy (dicionário de comparações)
    comparisons = {}
    for i in range(n):
        for j in range(i + 1, n):
            comparisons[(items[i], items[j])] = float(matrix[i][j])
    
    # Calcular com ahpy
    ahp = Compare('validation', comparisons, precision=6)
    
    # Extrair resultados na ordem correta
    weights = [ahp.target_weights[item] for item in items]
    
    return {
        'weights': weights,
        'cr': float(ahp.consistency_ratio) if ahp.consistency_ratio else 0,
        'lambda_max': float(ahp.eigenvalue) if ahp.eigenvalue else 0
    }

# ============================================================
# ENDPOINTS DA API
# ============================================================

@app.route('/', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'service': 'AHP Validator',
        'version': '1.0.0',
        'ahpy_available': AHPY_AVAILABLE
    })

@app.route('/validate', methods=['POST'])
def validate():
    """
    Endpoint principal de validação
    
    Recebe:
    {
        "matrix": [[1, 3, 5], [0.33, 1, 2], [0.2, 0.5, 1]],
        "items": ["A", "B", "C"],
        "your_weights": [0.637, 0.258, 0.105],
        "your_cr": 0.0158
    }
    
    Retorna comparação entre sistema e SDK
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        matrix = np.array(data.get('matrix', []))
        items = data.get('items', [])
        your_weights = data.get('your_weights', [])
        your_cr = data.get('your_cr', 0)
        your_lambda = data.get('your_lambda', 0)
        
        if len(matrix) == 0 or len(items) == 0:
            return jsonify({'error': 'Matrix and items are required'}), 400
        
        # Validar com implementação de referência
        ref_result = validate_with_reference(matrix, items)
        
        # Validar com ahpy se disponível
        ahpy_result = None
        if AHPY_AVAILABLE:
            try:
                ahpy_result = validate_with_ahpy(matrix, items)
            except Exception as e:
                ahpy_result = {'error': str(e)}
        
        # Comparar resultados
        sdk_weights = ref_result['weights']
        sdk_cr = ref_result['cr']
        sdk_lambda = ref_result['lambda_max']
        
        # Calcular diferenças
        if your_weights:
            diff_weights = [abs(a - b) for a, b in zip(your_weights, sdk_weights)]
            max_diff_weights = max(diff_weights) if diff_weights else 0
        else:
            diff_weights = []
            max_diff_weights = 0
        
        diff_cr = abs(your_cr - sdk_cr) if your_cr else 0
        diff_lambda = abs(your_lambda - sdk_lambda) if your_lambda else 0
        
        # Determinar se validação passou
        tolerance = 0.001  # 0.1%
        weights_valid = max_diff_weights < tolerance
        cr_valid = diff_cr < tolerance
        
        is_valid = weights_valid and cr_valid
        
        response = {
            'success': True,
            'validation': {
                'is_valid': is_valid,
                'tolerance': tolerance,
                'weights_valid': weights_valid,
                'cr_valid': cr_valid
            },
            'your_system': {
                'weights': your_weights,
                'cr': your_cr,
                'lambda_max': your_lambda
            },
            'reference': {
                'weights': sdk_weights,
                'cr': sdk_cr,
                'lambda_max': sdk_lambda,
                'method': 'geometric_mean',
                'methods_agree': ref_result['methods_agree']
            },
            'differences': {
                'weights': diff_weights,
                'max_weight_diff': max_diff_weights,
                'cr_diff': diff_cr,
                'lambda_diff': diff_lambda
            },
            'ahpy_available': AHPY_AVAILABLE,
            'ahpy_result': ahpy_result
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/validate-batch', methods=['POST'])
def validate_batch():
    """
    Validar múltiplas matrizes de uma vez
    Útil para validar BOCR + subcritérios + alternativas
    """
    try:
        data = request.json
        matrices = data.get('matrices', [])
        
        results = []
        all_valid = True
        
        for item in matrices:
            matrix = np.array(item.get('matrix', []))
            items = item.get('items', [])
            your_weights = item.get('your_weights', [])
            your_cr = item.get('your_cr', 0)
            name = item.get('name', 'Unknown')
            
            # Validar
            ref_result = validate_with_reference(matrix, items)
            
            # Comparar
            sdk_weights = ref_result['weights']
            sdk_cr = ref_result['cr']
            
            if your_weights:
                diff_weights = [abs(a - b) for a, b in zip(your_weights, sdk_weights)]
                max_diff = max(diff_weights)
            else:
                diff_weights = []
                max_diff = 0
            
            diff_cr = abs(your_cr - sdk_cr)
            
            is_valid = max_diff < 0.001 and diff_cr < 0.001
            if not is_valid:
                all_valid = False
            
            results.append({
                'name': name,
                'is_valid': is_valid,
                'your_weights': your_weights,
                'sdk_weights': sdk_weights,
                'your_cr': your_cr,
                'sdk_cr': sdk_cr,
                'max_weight_diff': max_diff,
                'cr_diff': diff_cr
            })
        
        return jsonify({
            'success': True,
            'all_valid': all_valid,
            'total': len(results),
            'passed': sum(1 for r in results if r['is_valid']),
            'failed': sum(1 for r in results if not r['is_valid']),
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/reference-cases', methods=['GET'])
def reference_cases():
    """
    Retorna casos de referência da literatura para auto-validação
    """
    cases = [
        {
            'name': 'Saaty (1980) - Drinks Example',
            'source': 'The Analytic Hierarchy Process, p.26',
            'matrix': [
                [1, 9, 5, 2, 1, 1, 0.5],
                [1/9, 1, 1/3, 1/9, 1/9, 1/9, 1/9],
                [0.2, 3, 1, 1/3, 0.25, 1/3, 1/9],
                [0.5, 9, 3, 1, 0.5, 1, 1/3],
                [1, 9, 4, 2, 1, 2, 0.5],
                [1, 9, 3, 1, 0.5, 1, 1/3],
                [2, 9, 9, 3, 2, 3, 1]
            ],
            'items': ['Coffee', 'Wine', 'Tea', 'Beer', 'Sodas', 'Milk', 'Water'],
            'expected_weights': [0.177, 0.019, 0.042, 0.116, 0.190, 0.129, 0.327],
            'expected_cr': 0.022
        },
        {
            'name': 'Saaty (1980) - 3x3 Simple',
            'source': 'Fundamentals of Decision Making',
            'matrix': [
                [1, 3, 5],
                [1/3, 1, 2],
                [0.2, 0.5, 1]
            ],
            'items': ['A', 'B', 'C'],
            'expected_weights': [0.637, 0.258, 0.105],
            'expected_cr': 0.0158
        },
        {
            'name': 'Wijnmalen (2007) - BOCR',
            'source': 'Mathematical and Computer Modelling, p.894',
            'matrix': [
                [1, 2, 3, 5],
                [0.5, 1, 2, 4],
                [1/3, 0.5, 1, 2],
                [0.2, 0.25, 0.5, 1]
            ],
            'items': ['Benefits', 'Opportunities', 'Costs', 'Risks'],
            'expected_weights': [0.488, 0.275, 0.158, 0.079],
            'expected_cr': 0.0157
        }
    ]
    
    return jsonify({
        'cases': cases,
        'note': 'Use these cases to validate your AHP implementation'
    })

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
