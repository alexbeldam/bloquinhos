db.scores.drop();

db.scores.insertMany([
	{
		name: 'elleWoods',
		score: 150000,
		lines: 120,
		level: 12,
		played_at: new Date(),
	},
	{
		name: 'pauletteBonafonte',
		score: 75000,
		lines: 85,
		level: 9,
		played_at: new Date(),
	},
	{
		name: 'bruiserWoods',
		score: 30000,
		lines: 45,
		level: 5,
		played_at: new Date(),
	},
	{
		name: 'emmet',
		score: 12000,
		lines: 20,
		level: 3,
		played_at: new Date(),
	},
	{
		name: 'deltaNu',
		score: 2500,
		lines: 5,
		level: 1,
		played_at: new Date(),
	},
]);

print('Database seeding completed successfully.');
