package com.cvr.cse.lecturesummarizer.services;

import com.cvr.cse.lecturesummarizer.models.Task;
import com.cvr.cse.lecturesummarizer.models.User;
import com.cvr.cse.lecturesummarizer.repositories.TaskRepository;
import com.cvr.cse.lecturesummarizer.repositories.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Service
public class TaskService {

    @Autowired
    private TaskRepository taskRepository;

    @Autowired
    private UserRepository userRepository;

    public List<Task> getUserTasks(String email, String status, String priority) {
        Optional<User> userOpt = userRepository.findByEmail(email);
        if (!userOpt.isPresent()) {
            throw new RuntimeException("User not found");
        }
        
        String userId = userOpt.get().getId();
        
        if (status != null) {
            return taskRepository.findByUserIdAndStatus(userId, status);
        }
        if (priority != null) {
            return taskRepository.findByUserIdAndPriority(userId, priority);
        }
        return taskRepository.findByUserIdOrderByCreatedAtDesc(userId);
    }

    public Task getTask(String id) {
        return taskRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Task not found"));
    }

    public Task createTask(String email, Task task) {
        Optional<User> userOpt = userRepository.findByEmail(email);
        if (!userOpt.isPresent()) {
            throw new RuntimeException("User not found");
        }
        
        task.setUserId(userOpt.get().getId());
        task.setCreatedAt(LocalDateTime.now());
        task.setUpdatedAt(LocalDateTime.now());
        
        return taskRepository.save(task);
    }

    public Task updateTask(String id, Task taskDetails) {
        Task task = getTask(id);
        
        task.setTitle(taskDetails.getTitle());
        task.setDescription(taskDetails.getDescription());
        task.setCourse(taskDetails.getCourse());
        task.setPriority(taskDetails.getPriority());
        task.setDeadline(taskDetails.getDeadline());
        task.setSubtasks(taskDetails.getSubtasks());
        task.setUpdatedAt(LocalDateTime.now());

        // Sync status and progress
        String oldStatus = task.getStatus();
        String newStatus = taskDetails.getStatus();
        task.setStatus(newStatus);

        if ("completed".equalsIgnoreCase(newStatus)) {
            task.setProgress(100);
        } else if ("in-progress".equalsIgnoreCase(newStatus)) {
            // If it was pending or 0, jump to 10% to show activity
            if (task.getProgress() == 0 || "pending".equalsIgnoreCase(oldStatus)) {
                task.setProgress(10);
            }
        } else if ("pending".equalsIgnoreCase(newStatus)) {
            // Optional: reset to 0 if moved back to pending? 
            // Usually safer to keep progress unless explicitly reset, but for this app's "Actionable" feel:
            if (task.getProgress() == 100) task.setProgress(90); 
        } else {
            task.setProgress(taskDetails.getProgress());
        }
        
        return taskRepository.save(task);
    }

    public void deleteTask(String id) {
        taskRepository.deleteById(id);
    }

    public void deleteMultipleTasks(List<String> ids) {
        taskRepository.deleteAllById(ids);
    }

    public void deleteAllUserTasks(String email) {
        Optional<User> userOpt = userRepository.findByEmail(email);
        if (userOpt.isPresent()) {
            taskRepository.deleteByUserId(userOpt.get().getId());
        }
    }
}