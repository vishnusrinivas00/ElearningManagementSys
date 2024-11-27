"use client";
import React, { useState, useEffect } from 'react';

interface Course {
  id: number;
  title: string;
  description: string;
}

interface Module {
  id?: number;
  course_id?: number;
  title: string;
  description: string;
  content?: string;
}

const CourseDetails: React.FC = () => {
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);
  const [modules, setModules] = useState<Module[]>([]);
  const [newModule, setNewModule] = useState<Module>({
    title: '',
    description: '',
    content: ''
  });
  const [newCourse, setNewCourse] = useState({ title: '', description: '' });
  const [userRole, setUserRole] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const role = localStorage.getItem('role');
    setUserRole(role || '');
    fetchCourses();
  }, []);

  const fetchCourses = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:5000/courses', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) throw new Error('Failed to fetch courses');
      
      const data = await response.json();
      setCourses(data);
    } catch (error) {
      setError('Error fetching courses');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const fetchModules = async (courseId: number) => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:5000/modules?course_id=${courseId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) throw new Error('Failed to fetch modules');
      
      const data = await response.json();
      setModules(data);
    } catch (error) {
      setError('Error fetching modules');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleCourseSelect = (course: Course) => {
    setSelectedCourse(course);
    fetchModules(course.id);
  };

  const handleAddModule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourse) return;

    try {
      const response = await fetch('http://localhost:5000/modules', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          ...newModule,
          course_id: selectedCourse.id
        })
      });

      if (!response.ok) throw new Error('Failed to add module');

      setMessage('Module added successfully!');
      setNewModule({ title: '', description: '', content: '' });
      fetchModules(selectedCourse.id);
    } catch (error) {
      setError('Error adding module');
      console.error(error);
    }
  };

  const handleCreateCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:5000/courses', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          ...newCourse,
          instructor_id: localStorage.getItem('user_id')
        }),
      });

      if (response.ok) {
        setMessage('Course created successfully!');
        setNewCourse({ title: '', description: '' });
        fetchCourses();
      } else {
        const data = await response.json();
        setMessage(data.error || 'Error creating course');
      }
    } catch (error) {
      setMessage('Server error. Please check your connection.');
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="text-red-500">{error}</div>;

  return (
    <div className="p-4">
      {/* Course Selection for Students */}
      {userRole === 'student' && !selectedCourse && (
        <div>
          <h2 className="text-2xl font-bold mb-4">Select a Course</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {courses.map(course => (
              <div 
                key={course.id} 
                className="bg-white rounded-lg shadow-md p-6 cursor-pointer hover:bg-blue-50"
                onClick={() => handleCourseSelect(course)}
              >
                <h3 className="text-xl font-bold">{course.title}</h3>
                <p className="text-gray-600">{course.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Module View for Students */}
      {userRole === 'student' && selectedCourse && (
        <div>
          <button 
            onClick={() => setSelectedCourse(null)} 
            className="mb-4 bg-blue-500 text-white px-4 py-2 rounded"
          >
            Back to Courses
          </button>
          <h2 className="text-2xl font-bold mb-4">{selectedCourse.title} Modules</h2>
          {modules.length === 0 ? (
            <p>No modules available for this course.</p>
          ) : (
            <div className="space-y-4">
              {modules.map(module => (
                <div key={module.id} className="bg-white rounded-lg shadow-md p-6">
                  <h3 className="text-xl font-semibold">{module.title}</h3>
                  <p className="text-gray-600">{module.description}</p>
                  {module.content && (
                    <div className="mt-4 bg-gray-100 p-4 rounded">
                      <pre className="whitespace-pre-wrap">{module.content}</pre>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Module Management for Instructors */}
      {userRole === 'instructor' && (
        <div>
          <h2 className="text-2xl font-bold mb-4">Course and Module Management</h2>
          {message && <div className="text-green-500 mb-4">{message}</div>}

          {/* Create New Course Form */}
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-2">Create a New Course</h3>
            <form onSubmit={handleCreateCourse} className="space-y-4">
              <input
                placeholder="Course Title"
                value={newCourse.title}
                onChange={(e) => setNewCourse({...newCourse, title: e.target.value})}
                className="w-full p-2 border rounded"
                required
              />
              <textarea
                placeholder="Course Description"
                value={newCourse.description}
                onChange={(e) => setNewCourse({...newCourse, description: e.target.value})}
                className="w-full p-2 border rounded"
                rows={3}
                required
              />
              <button
                type="submit"
                className="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
              >
                Create Course
              </button>
            </form>
          </div>

          {/* Course Selection for Instructor */}
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-2">Select a Course</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {courses.map(course => (
                <div 
                  key={course.id} 
                  className={`bg-white rounded-lg shadow-md p-6 cursor-pointer ${selectedCourse?.id === course.id ? 'bg-blue-100' : 'hover:bg-blue-50'}`}
                  onClick={() => handleCourseSelect(course)}
                >
                  <h3 className="text-xl font-bold">{course.title}</h3>
                  <p className="text-gray-600">{course.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Module Management */}
          {selectedCourse && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">Add Module to {selectedCourse.title}</h3>
              <form onSubmit={handleAddModule}>
                <input
                  type="text"
                  placeholder="Module Title"
                  value={newModule.title}
                  onChange={(e) => setNewModule({...newModule, title: e.target.value})}
                  className="w-full p-2 border rounded mb-4"
                  required
                />
                <textarea
                  placeholder="Module Description"
                  value={newModule.description}
                  onChange={(e) => setNewModule({...newModule, description: e.target.value})}
                  className="w-full p-2 border rounded mb-4"
                  rows={3}
                  required
                />
                <textarea
                  placeholder="Module Content"
                  value={newModule.content || ''}
                  onChange={(e) => setNewModule({...newModule, content: e.target.value})}
                  className="w-full p-2 border rounded mb-4"
                  rows={4}
                />
                <button
                  type="submit"
                  className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
                >
                  Add Module
                </button>
              </form>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CourseDetails;
