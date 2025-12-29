from todo_advanced_pkg import storage, query
import tempfile
storage.DB_FILE = tempfile.NamedTemporaryFile(delete=False).name
storage.initialize()
storage.add_task('buy milk', ['personal'])
storage.add_task('finish report', ['work','urgent'])
print('tasks:', storage.list_tasks())
s = 'tag:work AND (urgent OR personal)'
print('dsl:', s)
print('tokens:', query.tokenize(s))
print('tree:', query.Parser(query.tokenize(s)).parse())
print('execute ->', query.execute(s))
