#!/usr/bin/env python3
"""
Teste básico para verificar se a crew está funcionando
"""

# Código simples com alguns problemas para teste
class SimpleExample:
    """Exemplo simples com alguns problemas intencionais"""
    
    def __init__(self):
        self.data = []
        self.config = {}
        self.users = {}
        self.orders = {}
        self.reports = {}
    
    def processEverything(self, user_id, data, options):  # Naming violation
        """Método que faz muitas coisas - viola SRP"""
        
        # Validação
        if not user_id:
            return False
        
        if not data:
            return False
        
        # Processamento aninhado
        if user_id in self.users:
            if self.users[user_id].get('active'):
                if data.get('type') == 'order':
                    if data.get('items'):
                        if len(data['items']) > 0:
                            # Processar pedido
                            total = 0
                            for item in data['items']:
                                total += item.get('price', 0) * item.get('quantity', 1)
                            return total
                        else:
                            return 0
                    else:
                        return 0
                else:
                    return 0
            else:
                return False
        else:
            return False
    
    def send_email(self, user, message):  # Responsabilidade adicional
        print(f"Sending email to {user}: {message}")
    
    def generate_report(self):  # Outra responsabilidade
        return "Monthly report generated"
    
    def validate_data(self, data):  # Mais uma responsabilidade
        return isinstance(data, dict)

# Código duplicado
def calculate_discount_v1(price, user_type):
    if user_type == "premium":
        return price * 0.1
    elif user_type == "gold":
        return price * 0.15
    else:
        return 0

def calculate_discount_v2(price, user_type):
    if user_type == "premium":
        return price * 0.1
    elif user_type == "gold":
        return price * 0.15
    else:
        return 0