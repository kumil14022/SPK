from http import HTTPStatus
from flask import Flask, request, abort
from flask_restful import Resource, Api 
from models import Karyawan as KaryawanModel
from engine import engine
from sqlalchemy import select
from sqlalchemy.orm import Session

session = Session(engine)

app = Flask(__name__)
api = Api(app)        

class BaseMethod():

    def __init__(self):
        self.raw_weight = {'umur': 4, 'jenis_kelamin': 2, 'status_pernikahan': 3, 'pengalaman': 5, 'pengetahuan': 5}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(KaryawanModel.id, KaryawanModel.umur, KaryawanModel.jenis_kelamin, KaryawanModel.status_pernikahan, KaryawanModel.pengalaman, KaryawanModel.pengetahuan)
        result = session.execute(query).fetchall()
        print(result)
        return [{'id': ponsel.id, 'umur': ponsel.umur, 'jenis_kelamin': ponsel.jenis_kelamin, 'status_pernikahan': ponsel.status_pernikahan, 'pengalaman': ponsel.pengalaman, 'pengetahuan': ponsel.pengetahuan} for ponsel in result]

    @property
    def normalized_data(self):
        umur_values = []
        jenis_kelamin_values = []
        status_pernikahan_values = []
        pengalaman_values = []
        pengetahuan_values = []

        for data in self.data:
            umur_values.append(data['umur'])
            jenis_kelamin_values.append(data['jenis_kelamin'])
            status_pernikahan_values.append(data['status_pernikahan'])
            pengalaman_values.append(data['pengalaman'])
            pengetahuan_values.append(data['pengetahuan'])

        return [
            {'id': data['id'],
             'umur': min(umur_values) / data['umur'],
             'jenis_kelamin': data['jenis_kelamin'] / max(jenis_kelamin_values),
             'status_pernikahan': data['status_pernikahan'] / max(status_pernikahan_values),
             'pengalaman': data['pengalaman'] / max(pengalaman_values),
             'pengetahuan': data['pengetahuan'] / max(pengetahuan_values)
             }
            for data in self.data
        ]

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class WeightedProductCalculator(BaseMethod):
    def update_weights(self, new_weights):
        self.raw_weight = new_weights

    @property
    def calculate(self):
        normalized_data = self.normalized_data
        produk = []

        for row in normalized_data:
            product_score = (
                row['umur'] ** self.raw_weight['umur'] *
                row['jenis_kelamin'] ** self.raw_weight['jenis_kelamin'] *
                row['status_pernikahan'] ** self.raw_weight['status_pernikahan'] *
                row['pengalaman'] ** self.raw_weight['pengalaman'] *
                row['pengetahuan'] ** self.raw_weight['pengetahuan']
            )

            produk.append({
                'id': row['id'],
                'produk': product_score
            })

        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)

        sorted_data = []

        for product in sorted_produk:
            sorted_data.append({
                'id': product['id'],
                'score': product['produk']
            })

        return sorted_data


class WeightedProduct(Resource):
    def get(self):
        calculator = WeightedProductCalculator()
        result = calculator.calculate
        return result, HTTPStatus.OK.value
    
    def post(self):
        new_weights = request.get_json()
        calculator = WeightedProductCalculator()
        calculator.update_weights(new_weights)
        result = calculator.calculate
        return {'data': result}, HTTPStatus.OK.value
    

class SimpleAdditiveWeightingCalculator(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = {row['id']:
                  round(row['umur'] * weight['umur'] +
                        row['jenis_kelamin'] * weight['jenis_kelamin'] +
                        row['status_pernikahan'] * weight['status_pernikahan'] +
                        row['pengalaman'] * weight['pengalaman'] +
                        row['pengetahuan'] * weight['pengetahuan'], 2)
                  for row in self.normalized_data
                  }
        sorted_result = dict(
            sorted(result.items(), key=lambda x: x[1], reverse=True))
        return sorted_result

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class SimpleAdditiveWeighting(Resource):
    def get(self):
        saw = SimpleAdditiveWeightingCalculator()
        result = saw.calculate
        return result, HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        saw = SimpleAdditiveWeightingCalculator()
        saw.update_weights(new_weights)
        result = saw.calculate
        return {'data': result}, HTTPStatus.OK.value


class Karyawan(Resource):
    def get_paginated_result(self, url, list, args):
        page_size = int(args.get('page_size', 10))
        page = int(args.get('page', 1))
        page_count = int((len(list) + page_size - 1) / page_size)
        start = (page - 1) * page_size
        end = min(start + page_size, len(list))

        if page < page_count:
            next_page = f'{url}?page={page+1}&page_size={page_size}'
        else:
            next_page = None
        if page > 1:
            prev_page = f'{url}?page={page-1}&page_size={page_size}'
        else:
            prev_page = None
        
        if page > page_count or page < 1:
            abort(404, description=f'Halaman {page} tidak ditemukan.') 
        return {
            'page': page, 
            'page_size': page_size,
            'next': next_page, 
            'prev': prev_page,
            'Results': list[start:end]
        }

    def get(self):
        query = select(KaryawanModel)
        data = [{'id': ponsel.id, 'umur': ponsel.umur, 'jenis_kelamin': ponsel.jenis_kelamin, 'status_pernikahan': ponsel.status_pernikahan, 'pengalaman': ponsel.pengalaman, 'pengetahuan': ponsel.pengetahuan} for ponsel in session.scalars(query)]
        return self.get_paginated_result('ponsel/', data, request.args), HTTPStatus.OK.value


api.add_resource(Karyawan, '/karyawan')
api.add_resource(WeightedProduct, '/wp')
api.add_resource(SimpleAdditiveWeighting, '/saw')

if __name__ == '__main__':
    app.run(port='5005', debug=True)
