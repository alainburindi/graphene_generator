import graphene
from django.conf import settings
from graphene_django.types import DjangoObjectType
from django.utils.module_loading import import_string
from graphql import GraphQLError


def make_resolver(model, query_type):
    """
    Make a query resolver.

    Parameters:
    model (dict): the model dictionary from settings
    query_type (str): to differentiate get all from get single

    Returns:
    function: the query resolver
    """

    model_class = import_string(model['path'])
    primary_key_column = model_class._meta.pk.name

    def _resolver(self, info, **kwargs):
        check_authentication(model, "queries", query_type, info)
        if query_type == "single":
            return model_class.objects.get(pk=kwargs.get(primary_key_column))
        else:
            return model_class.objects.all()

    return _resolver


def check_authentication(model, schema_type, context, info):
    """
    Check auth if authentication is required. Raise GraphQLError
    if the use is not authenticated

    Parameters:
    model (dict): the model dictionary from settings
    schema_type (str): either queries or mutations
    context (str): the request context (all, single, create, update, delete)

    Returns:
    pass: if require_auth is not provided
    """

    try:
        if context in model["require_auth"][schema_type]:
            if not info.context.user.is_authenticated:
                raise GraphQLError(
                    "You do not have permission to perform this action")
    except KeyError:
        # when the require_auth is not defined
        pass


def generate_mutation(model, mutation_type):
    """
    Generate a model mutation.
    Create the mutation class

    Parameters:
    model (dict): the model dictionary from settings
    mutation_type (str): the mutation type (create, delete, update)

    Returns:
    graphene.Mutation.Field: the mutation field
    """

    mutation_class_name = "{}{}".format(
        model['name'].title(), mutation_type.title())
    model_class = import_string(model['path'])

    arguments = get_arguments(model_class, mutation_type)
    mutate = get_mutate(model, mutation_type, model_class, mutation_class_name)

    # create the mutation class
    globals()[mutation_class_name] = type(mutation_class_name, (graphene.Mutation,), {
        '__module__': __name__,
        "Arguments": type("Arguments", (), arguments),
        "message": graphene.String(),
        "ingredient": graphene.Field(globals()["{}Type".format(model['name'].title())]),
        "mutate": mutate
    })

    return globals()[mutation_class_name].Field()


def get_mutate(model, mutation_type, model_class, mutation_class_name):
    """
    Generates the mutate function.

    Parameters:
    model (dict): the model dictionary from settings
    mutation_type (str): the mutation type (create, delete, update)
    model_class (Model): the imported model from the path
    mutation_class_name (graphene.Mutation): the generated mutation's class

    Returns:
    function: mutate
    """

    def _mutate(self, info, **kwargs):
        check_authentication(model, "mutations", mutation_type, info)
        model_instance = None
        if mutation_type == "create":
            model_instance = model_class()
        else:
            primary_key_column = model_class._meta.pk.name
            model_instance = model_class.objects.get(
                pk=kwargs.get(primary_key_column))

        if mutation_type != "delete":
            for key, value in kwargs.items():
                setattr(model_instance, key, value)
            model_instance.save()
        else:
            model_instance.delete()

        message = "{} has been {}d successfully".format(
            model["name"], mutation_type)

        return globals()[mutation_class_name](message, model_instance)

    return _mutate


def get_arguments(model, mutation_type):
    """
    Get mutation arguments based on the model

    Parameters:
    model (dict): the model dictionary from settings
    mutation_type (str): the mutation type (create, delete, update)

    Returns:
    dict: the mutation arguments
    """

    arguments = {}
    if mutation_type == "create":
        for field in model._meta.get_fields():
            # skip auto created fields
            if not field.auto_created:
                arguments[field.name] = graphene.String(
                    required=not field.null)
    elif mutation_type == "update":
        # only the pk will be required
        for field in model._meta.get_fields():
            arguments[field.name] = graphene.String(
                required=True if field.name == model._meta.pk.name else False)
    else:
        arguments[model._meta.pk.name] = graphene.String(
            required=True
        )
    return arguments


class QueriesHolder(graphene.ObjectType):
    """
    This is a class that holds all model's generated queries. 
    """

    for model in settings.GRAPHENE_GENERATOR_MODELS:
        model_type_name = "{}Type".format(model['name'].title())
        modelInstance = import_string(model['path'])
        # generate the model object type
        globals()[model_type_name] =\
            type(model_type_name, (DjangoObjectType,), {'__module__': __name__,
                                                        "Meta":
                                                        type("Meta", (), {"model": modelInstance})})
        # queries
        exec("%s = %s" %
             (model['name']+"s", "graphene.List({})".format(model_type_name)))
        exec("%s = %s" %
             (model['name'], "graphene.Field({}, {}  = graphene.String(required=True))".
              format(model_type_name, modelInstance._meta.pk.name)))
        # generate resolvers
        exec("%s = %s" %
             ("resolve_{}s".format(model["name"]), "make_resolver(model, 'all')"))
        exec("%s = %s" %
             ("resolve_{}".format(model["name"]), "make_resolver(model, 'single')"))


class MutationsHolder(graphene.ObjectType):
    """
    This is a class that holds all model's generated mutation.
    """

    for model in settings.GRAPHENE_GENERATOR_MODELS:
        exec("%s = %s" %
             ("create_{}".format(model["name"].lower()),
              "generate_mutation(model, 'create')"))
        exec("%s = %s" %
             ("update_{}".format(model["name"].lower()),
              "generate_mutation(model, 'update')"))
        exec("%s = %s" %
             ("delete_{}".format(model["name"].lower()),
              "generate_mutation(model, 'delete')"))
