# Utility function definitions
def obj2dict(query_results):
	'''Convert the query result to type "dict".

	Parameters:
		query_results: list, a list of query results

	Return:
		query_dicts: list, a list of query results with type "dict"
	'''
	query_dicts = []
	for query_result in query_results:
		query_dict = {}
		for col in query_result.__table__.columns:
			query_dict[col.name] = str(getattr(query_result, col.name))
		query_dicts.append(query_dict)

	return query_dicts