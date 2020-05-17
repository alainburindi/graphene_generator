## Graphene-Generator

A [Graphene-Django](https://github.com/graphql-python/graphene-django) (GraphQL) queries and mutations generator

### You can:

- Generate queries and mutations based on the specified model(s)
- Require authentication for some and/or all generated queries/mutations

### Tech

Graphene-Generator uses a number of open source projects to work properly:

- [Django](https://github.com/django/django) - a Python-based web framework,
- [Graphene-Django](https://github.com/graphql-python/graphene-django) - A Django integration for Graphene.

If you are not familiar with the above technologies, please refer to their respective documentation.

And of course Graphene-generator itself is open source with a [public repository](https://github.com/alainburindi/django-gphql-api-generator) on GitHub.

### Quickstart

For installing graphene, just run this command in your shell:

```bash
pip install "graphene-generator"
```

#### Settings

We need to specify the model(s) name to be used and their respective path(s)

```python
    GRAPHENE_GENERATOR_MODELS = [
        {
            'name': 'ingredient',
            'path': 'path.to.the.model',
        }
    ]
```

Note that `GRAPHENE_GENERATOR_MODELS` is an array to support many models at once.

#### Authentication

If we want to require the authentication, we need to specify that in our settings under the `require_auth` dictionary for each model

```python
    GRAPHENE_GENERATOR_MODELS = [
        {
            # ...
            'require_auth': {
                'queries': ["all", "single"],
                'mutations': ["create", 'update', 'delete']
            }
        }
    ]
```

To make the difference between Mutations and Queries the `require_auth` contains `queries` and `mutations` as different keys.

Below are the different values and their meaning:

##### Queries

| Key word | Meaning                                             |
| -------- | --------------------------------------------------- |
| `all`    | The get all query (usually the `model['name'] + s`) |
| `single` | The get one query (usually the `model['name']`)     |

##### Mutations

| Key word | Meaning             |
| -------- | ------------------- |
| `create` | The create mutation |
| `update` | The update mutation |
| `delete` | The delete mutation |

#### Schema

We need to import the `QueriesHolder` and/or `MutationsHolder` classes into our schema used by graphene and you should be able to see the generated CRUD operations into you schema.

## Examples

Here is a simple Django model:

```python
from django.db import models

class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    notes = models.TextField()
```

Based on the above model ou settings would look like:

```python
GRAPHENE_GENERATOR_MODELS = [
    {
        'name': 'ingredient',
        'path': 'ingredients.models.Ingredient',
        'require_auth': {
            'queries': ["all", "single"],
            'mutations': ["create", 'update', 'delete']
        }
    }
]
```

Here is a graphene schema sample which use the generated requests:

```python
import graphene

from generator import QueriesHolder, MutationsHolder


class Query(QueriesHolder, graphene.ObjectType):
    pass


class Mutation(MutationsHolder, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=MutationsHolder)
```

Then you can query the schema:

```python
query = '''
    query {
      ingredients {
        name,
        notes
      }
    }
'''
result = schema.execute(query)
```

### Todos

- Write Tests
- Handle model's relations properly
- Use corresponding graphene scalar type for each field(currently using string for all fields)
- Handle pagination

## License

MIT
