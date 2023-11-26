"""
Schema for GraphQL apis for the UNS
"""
import graphene

from uns_graphql.type import Node


class Query(graphene.ObjectType):
    """

    """
    allTopics = graphene.List(Node)
    specificTopics = graphene.List(Node,
                                   topics=graphene.List(graphene.String,
                                                        required=True))

    async def resolve_allTopics(self, info):
        # Placeholder logic to fetch all topics from Neo4j
        # Implement actual logic in resolvers.py
        return []

    async def resolve_specificTopics(self, info, topics):
        # Placeholder logic to fetch specific topics data from different sources
        # Implement actual logic in resolvers.py
        return []


schema = graphene.Schema(query=Query)
