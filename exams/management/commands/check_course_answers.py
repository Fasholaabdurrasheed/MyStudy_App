from django.core.management.base import BaseCommand
from exams.models import CourseAnswer, CourseQuestion

class Command(BaseCommand):
    help = 'Check for invalid CourseAnswer.question references'

    def handle(self, *args, **kwargs):
        invalid_answers = []

        for answer in CourseAnswer.objects.all():
            if not isinstance(answer.question, CourseQuestion):
                invalid_answers.append(answer)
                self.stdout.write(self.style.WARNING(
                    f"Invalid answer ID {answer.id}: question is not a CourseQuestion instance"
                ))
            else:
                try:
                    # Further check if the related question exists
                    _ = answer.question.id  # Will raise if related object is missing
                except CourseQuestion.DoesNotExist:
                    invalid_answers.append(answer)
                    self.stdout.write(self.style.WARNING(
                        f"Broken FK: CourseQuestion for answer ID {answer.id} does not exist"
                    ))

        if invalid_answers:
            self.stdout.write(self.style.ERROR(
                f"\nFound {len(invalid_answers)} invalid CourseAnswer entries."
            ))

            # Optional cleanup
            confirm = input("Do you want to delete these invalid entries? (yes/no): ").lower()
            if confirm == 'yes':
                for entry in invalid_answers:
                    entry.delete()
                self.stdout.write(self.style.SUCCESS("Invalid entries deleted."))
            else:
                self.stdout.write("No entries deleted.")
        else:
            self.stdout.write(self.style.SUCCESS("No invalid CourseAnswer entries found."))
